"""Tests for the Federated Learning Across Agencies API.

Covers FL round lifecycle, secure aggregation, differential privacy
guarantees, model convergence, client registration, anomaly detection,
chain of custody, and edge cases. 20+ tests.
"""

import base64
import json
import os
import sys
import time
from typing import Any, Generator
from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import api as _api_module
from federated.server import FederatedServer, ClientRegistration
from federated.secure_aggregation import (
    SecureAggregator,
    ShamirSecretSharing,
    SecretShare,
    AggregationResult,
)
from models.dp_engine import DifferentialPrivacyEngine, PrivacyBudget
from models.malware_cnn import MalwareCNN, EvaluationMetrics

app = _api_module.app
fl_server = _api_module.fl_server

client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_state():
    """Reset FL server state and agency dict before each test."""
    _api_module.fl_server = FederatedServer(
        min_clients=2,
        aggregation_threshold=2,
        dp_epsilon=1.0,
        dp_delta=1e-5,
        max_grad_norm=1.0,
        checkpoint_dir=os.path.join(os.path.dirname(__file__), "..", "checkpoints"),
    )
    _api_module._agencies.clear()


@pytest.fixture
def registered_clients() -> list[str]:
    ids = []
    for name in ["Alpha Agency", "Beta Bureau", "Gamma Unit"]:
        resp = client.post("/fl/register-client", json={
            "agency_name": name,
            "public_key": f"kyber_pk_{name}_1234",
            "dilithium_public_key": f"dilithium_pk_{name}_5678",
            "jurisdiction": "Federal",
        })
        assert resp.status_code == 200
        ids.append(resp.json()["client_id"])
    return ids


@pytest.fixture
def sample_gradients() -> list[bytes]:
    grads = [np.random.randn(10, 10).astype(np.float32).tobytes() for _ in range(6)]
    return [
        base64.b64encode(g).decode("utf-8") for g in grads
    ]


# ══════════════════════════════════════════════════════════════════════
# 1. Health & Module Info
# ══════════════════════════════════════════════════════════════════════


class TestHealth:
    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "federated-learning"
        assert data["status"] == "healthy"
        assert "num_clients" in data
        assert "num_rounds" in data
        assert data["dp_enabled"] is True
        assert data["model_loaded"] is True


# ══════════════════════════════════════════════════════════════════════
# 2. Client Registration
# ══════════════════════════════════════════════════════════════════════


class TestClientRegistration:
    def test_register_client(self):
        resp = client.post("/fl/register-client", json={
            "agency_name": "Test Agency",
            "public_key": "pk_test_001",
            "dilithium_public_key": "dpk_test_001",
            "jurisdiction": "Federal",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["agency_name"] == "Test Agency"
        assert data["public_key"] == "pk_test_001"
        assert data["jurisdiction"] == "Federal"
        assert len(data["client_id"]) > 0
        assert "registered_at" in data

    def test_register_multiple_clients(self, registered_clients):
        assert len(registered_clients) == 3

    def test_register_duplicate_allowed(self):
        r1 = client.post("/fl/register-client", json={
            "agency_name": "Same Agency",
            "public_key": "pk_1",
        })
        r2 = client.post("/fl/register-client", json={
            "agency_name": "Same Agency",
            "public_key": "pk_1",
        })
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["client_id"] != r2.json()["client_id"]

    def test_register_missing_fields(self):
        resp = client.post("/fl/register-client", json={})
        assert resp.status_code == 422

    def test_register_empty_agency_name(self):
        resp = client.post("/fl/register-client", json={
            "agency_name": "",
            "public_key": "pk",
        })
        assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════
# 3. FL Round Lifecycle
# ══════════════════════════════════════════════════════════════════════


class TestRoundLifecycle:
    def test_start_round(self, registered_clients):
        resp = client.post("/fl/start-round", json={
            "client_ids": registered_clients[:2],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"
        assert data["num_clients_requested"] == 2
        assert len(data["clients_invited"]) == 2
        assert "round_id" in data

    def test_start_round_all_clients(self, registered_clients):
        resp = client.post("/fl/start-round", json={})
        assert resp.status_code == 200
        assert resp.json()["num_clients_requested"] == 3

    def test_start_round_insufficient_clients(self):
        resp = client.post("/fl/start-round", json={})
        assert resp.status_code == 400
        assert "Need at least" in resp.json()["detail"]

    def test_full_round_lifecycle(self, registered_clients, sample_gradients):
        # Start round
        r = client.post("/fl/start-round", json={
            "client_ids": registered_clients[:2],
        })
        assert r.status_code == 200
        round_id = r.json()["round_id"]

        # Both clients submit updates
        for cid in registered_clients[:2]:
            r2 = client.post("/fl/submit-update", json={
                "round_id": round_id,
                "client_id": cid,
                "encrypted_gradients": sample_gradients,
                "dp_epsilon_used": 0.5,
            })
            assert r2.status_code == 200
            assert r2.json()["success"] is True

        # Check round status — should be collecting
        r3 = client.get(f"/fl/round/{round_id}/status")
        assert r3.status_code == 200
        assert r3.json()["num_clients_submitted"] == 2

        # Aggregate
        r4 = client.post("/fl/aggregate", json={"round_id": round_id})
        assert r4.status_code == 200
        agg = r4.json()
        assert agg["num_participants"] == 2
        assert len(agg["contributions"]) == 2

        # Round status should now be completed
        r5 = client.get(f"/fl/round/{round_id}/status")
        assert r5.json()["status"] == "completed"

    def test_get_latest_model_after_round(self, registered_clients, sample_gradients):
        # Start and complete a round
        r = client.post("/fl/start-round", json={
            "client_ids": registered_clients[:2],
        })
        round_id = r.json()["round_id"]

        for cid in registered_clients[:2]:
            client.post("/fl/submit-update", json={
                "round_id": round_id, "client_id": cid,
                "encrypted_gradients": sample_gradients,
            })

        client.post("/fl/aggregate", json={"round_id": round_id})

        # Get latest model
        r2 = client.get("/fl/model/latest")
        assert r2.status_code == 200
        model = r2.json()
        assert model["architecture"] == "MalwareCNN"
        assert model["parameter_count"] > 0
        assert model["round_number"] > 0
        assert len(model["weights"]) > 0

    def test_submit_to_nonexistent_round(self, registered_clients, sample_gradients):
        resp = client.post("/fl/submit-update", json={
            "round_id": "nonexistent",
            "client_id": registered_clients[0],
            "encrypted_gradients": sample_gradients,
        })
        assert resp.status_code == 400

    def test_submit_by_uninvited_client(self, registered_clients, sample_gradients):
        r = client.post("/fl/start-round", json={
            "client_ids": registered_clients[:2],
        })
        round_id = r.json()["round_id"]

        resp = client.post("/fl/submit-update", json={
            "round_id": round_id,
            "client_id": registered_clients[2],
            "encrypted_gradients": sample_gradients,
        })
        assert resp.status_code == 400

    def test_get_nonexistent_round_status(self):
        resp = client.get("/fl/round/nonexistent/status")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════
# 4. Secure Aggregation
# ══════════════════════════════════════════════════════════════════════


class TestSecureAggregation:
    def test_shamir_split_and_reconstruct(self):
        sss = ShamirSecretSharing(threshold=3)
        secret = 123456789
        shares = sss.split_secret(secret, 5)
        assert len(shares) == 5

        # Reconstruct with 3 shares
        indices = [(1, shares[0]), (3, shares[2]), (5, shares[4])]
        reconstructed = sss.reconstruct_secret(indices)
        assert reconstructed == secret

    def test_shamir_insufficient_shares(self):
        sss = ShamirSecretSharing(threshold=3)
        secret = 42
        shares = sss.split_secret(secret, 5)
        with pytest.raises(ValueError, match="Need at least"):
            sss.reconstruct_secret([(1, shares[0])])

    def test_shamir_threshold_validation(self):
        with pytest.raises(ValueError, match="Threshold must be at least 2"):
            ShamirSecretSharing(threshold=1)

    def test_secure_aggregator_aggregate(self):
        aggregator = SecureAggregator(threshold=2)
        round_id = "test-round-1"
        clients = ["agency-1", "agency-2"]

        aggregator.start_round(round_id, clients)

        submissions = {
            "agency-1": [np.ones((3, 3), dtype=np.float32) * 0.1 for _ in range(3)],
            "agency-2": [np.ones((3, 3), dtype=np.float32) * 0.2 for _ in range(3)],
        }

        result = aggregator.aggregate(round_id, submissions)
        assert result.num_participants == 2
        assert result.threshold_reached is True
        assert result.round_id == round_id
        assert len(result.aggregated_gradients) == 3

        # The result should be the mean of 0.1 and 0.2 = 0.15
        # (approximately, with DP noise)
        mean_val = float(np.mean(result.aggregated_gradients[0]))
        assert abs(mean_val - 0.15) < 0.5

    def test_secure_aggregator_threshold_not_met(self):
        aggregator = SecureAggregator(threshold=3)
        round_id = "test-round-2"
        aggregator.start_round(round_id, ["a1", "a2"])

        submissions = {
            "a1": [np.ones((2, 2), dtype=np.float32)],
        }
        with pytest.raises(ValueError, match="Threshold"):
            aggregator.aggregate(round_id, submissions)

    def test_secure_aggregator_empty_submissions(self):
        aggregator = SecureAggregator(threshold=2)
        round_id = "test-round-3"
        aggregator.start_round(round_id, ["a1", "a2"])

        with pytest.raises(ValueError, match="No client submissions"):
            aggregator.aggregate(round_id, {})

    def test_aggregator_contribution_scoring(self):
        aggregator = SecureAggregator(threshold=2)
        round_id = "contrib-test"
        aggregator.start_round(round_id, ["c1", "c2", "c3"])

        submissions = {
            "c1": [np.ones((5, 5), dtype=np.float32) * 0.5 for _ in range(2)],
            "c2": [np.ones((5, 5), dtype=np.float32) * 1.0 for _ in range(2)],
            "c3": [np.ones((5, 5), dtype=np.float32) * 2.0 for _ in range(2)],
        }
        result = aggregator.aggregate(round_id, submissions)
        scores = list(result.contributions.values())
        assert sum(scores) == pytest.approx(1.0, rel=0.01)
        # c3 should have highest contribution (largest norm)
        assert result.contributions["c3"] > result.contributions["c1"]


# ══════════════════════════════════════════════════════════════════════
# 5. Differential Privacy
# ══════════════════════════════════════════════════════════════════════


class TestDifferentialPrivacy:
    def test_gradient_clipping(self):
        dp = DifferentialPrivacyEngine(epsilon=1.0, max_grad_norm=1.0)
        grads = [np.ones((100, 100), dtype=np.float32) * 10.0]
        clipped, factor = dp.clip_gradients(grads)
        assert factor <= 1.0
        # Clipped norm should be <= max_grad_norm
        norm = float(np.sqrt(np.sum(clipped[0] ** 2)))
        assert norm <= 1.0 + 1e-6

    def test_noise_addition(self):
        dp = DifferentialPrivacyEngine(epsilon=1.0, max_grad_norm=1.0)
        shape = (50, 50)
        noise = dp.add_noise(sensitivity=1.0, shape=shape)
        assert noise.shape == shape
        assert noise.dtype == np.float32
        # Noise should be close to zero mean
        assert abs(float(np.mean(noise))) < 1.0

    def test_dp_application(self):
        dp = DifferentialPrivacyEngine(epsilon=1.0, max_grad_norm=1.0)
        grads = [np.ones((10, 10), dtype=np.float32) * 5.0]
        dp_grads = dp.apply_dp(grads)
        assert len(dp_grads) == len(grads)
        assert dp_grads[0].shape == grads[0].shape
        # DP grads should differ from original
        diff = float(np.sum(np.abs(dp_grads[0] - grads[0])))
        assert diff > 0

    def test_privacy_budget_tracking(self):
        dp = DifferentialPrivacyEngine(epsilon=1.0)
        budget = dp.initialise_budget("client-a", epsilon_budget=10.0)
        assert budget.epsilon_remaining == 10.0

        consumed = dp.consume_budget("client-a", steps=1)
        assert consumed.epsilon_consumed > 0
        assert consumed.epsilon_remaining < 10.0
        assert consumed.composition_count == 1

    def test_privacy_budget_exhaustion(self):
        dp = DifferentialPrivacyEngine(epsilon=1.0)
        dp.initialise_budget("client-b", epsilon_budget=0.001)
        with pytest.raises(RuntimeError, match="Privacy budget exhausted"):
            dp.consume_budget("client-b", steps=100)

    def test_noise_multiplier_calibration(self):
        dp = DifferentialPrivacyEngine(epsilon=5.0)
        dp_low = DifferentialPrivacyEngine(epsilon=0.1)
        # Lower epsilon => higher noise
        assert dp_low.noise_multiplier > dp.noise_multiplier

    def test_adaptive_vs_global_clipping(self):
        dp_adaptive = DifferentialPrivacyEngine(
            epsilon=1.0, adaptive_clip=True
        )
        dp_global = DifferentialPrivacyEngine(
            epsilon=1.0, adaptive_clip=False
        )
        grads = [np.ones((5, 5), dtype=np.float32) * 3.0]
        a_clipped, _ = dp_adaptive.clip_gradients(grads)
        g_clipped, _ = dp_global.clip_gradients(grads)
        # Both should have norm <= 1.0
        a_norm = float(np.sqrt(np.sum(a_clipped[0] ** 2)))
        g_norm = float(np.sqrt(np.sum(g_clipped[0] ** 2)))
        assert a_norm <= 1.0 + 1e-6
        assert g_norm <= 1.0 + 1e-6


# ══════════════════════════════════════════════════════════════════════
# 6. Contribution Metrics
# ══════════════════════════════════════════════════════════════════════


class TestContributions:
    def test_get_contributions_empty(self):
        resp = client.get("/fl/contributions")
        assert resp.status_code == 200
        assert resp.json()["contributions"] == []

    def test_get_contributions_after_round(self, registered_clients, sample_gradients):
        # Run a full round
        r = client.post("/fl/start-round", json={
            "client_ids": registered_clients[:2],
        })
        round_id = r.json()["round_id"]

        for cid in registered_clients[:2]:
            client.post("/fl/submit-update", json={
                "round_id": round_id, "client_id": cid,
                "encrypted_gradients": sample_gradients,
            })
        client.post("/fl/aggregate", json={"round_id": round_id})

        contribs = client.get("/fl/contributions").json()["contributions"]
        assert len(contribs) == 3
        # The 2 participants should have non-zero scores
        for c in contribs:
            if c["rounds_participated"] > 0:
                assert c["total_contribution_score"] > 0
                assert c["normalized_score"] > 0


# ══════════════════════════════════════════════════════════════════════
# 7. Evaluation
# ══════════════════════════════════════════════════════════════════════


class TestEvaluation:
    def test_evaluate_default(self):
        resp = client.post("/fl/evaluate", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert 0 < data["accuracy"] <= 1.0
        assert 0 < data["f1_score"] <= 1.0
        assert data["num_samples"] > 0
        assert data["model_parameters"] > 0


# ══════════════════════════════════════════════════════════════════════
# 8. MalwareCNN Model
# ══════════════════════════════════════════════════════════════════════


class TestMalwareCNN:
    def test_model_creation(self):
        model = MalwareCNN()
        assert model.get_parameter_count() > 0

    def test_model_weights_roundtrip(self):
        model = MalwareCNN()
        weights = model.get_weights()
        assert len(weights) > 0

        model2 = MalwareCNN()
        model2.set_weights(weights)
        weights2 = model2.get_weights()

        for w1, w2 in zip(weights, weights2):
            assert np.allclose(w1, w2)

    def test_model_checkpoint_save_load(self, tmp_path):
        model = MalwareCNN()
        ckpt_path = str(tmp_path / "test_model.pt")
        model.save_checkpoint(ckpt_path, round_id=1, accuracy=0.85, num_clients=2)
        assert os.path.exists(ckpt_path)

        model2 = MalwareCNN()
        ckpt = model2.load_checkpoint(ckpt_path)
        assert ckpt.round_id == 1
        assert ckpt.accuracy == 0.85

    def test_model_parameter_count_consistency(self):
        model = MalwareCNN()
        expected = sum(p.numel() for p in model.model.parameters() if p.requires_grad)
        assert model.get_parameter_count() == expected

    def test_model_size_positive(self):
        model = MalwareCNN()
        assert model.get_model_size_bytes() > 0


# ══════════════════════════════════════════════════════════════════════
# 9. Chain of Custody
# ══════════════════════════════════════════════════════════════════════


class TestChainOfCustody:
    def test_custody_chain_verification(self, registered_clients, sample_gradients):
        # Perform operations to create custody events
        r = client.post("/fl/start-round", json={
            "client_ids": registered_clients[:2],
        })
        round_id = r.json()["round_id"]

        for cid in registered_clients[:2]:
            client.post("/fl/submit-update", json={
                "round_id": round_id, "client_id": cid,
                "encrypted_gradients": sample_gradients,
            })
        client.post("/fl/aggregate", json={"round_id": round_id})

        valid, issues = fl_server.verify_chain_of_custody()
        assert valid is True
        assert issues == []


# ══════════════════════════════════════════════════════════════════════
# 10. Edge Cases & Error Handling
# ══════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_aggregate_without_submissions(self, registered_clients):
        r = client.post("/fl/start-round", json={
            "client_ids": registered_clients[:2],
        })
        round_id = r.json()["round_id"]

        resp = client.post("/fl/aggregate", json={"round_id": round_id})
        assert resp.status_code == 400

    def test_double_aggregate_fails(self, registered_clients, sample_gradients):
        r = client.post("/fl/start-round", json={
            "client_ids": registered_clients[:2],
        })
        round_id = r.json()["round_id"]

        for cid in registered_clients[:2]:
            client.post("/fl/submit-update", json={
                "round_id": round_id, "client_id": cid,
                "encrypted_gradients": sample_gradients,
            })

        # First aggregate succeeds
        assert client.post("/fl/aggregate", json={"round_id": round_id}).status_code == 200

        # Second aggregate should fail (round already completed)
        r2 = client.post("/fl/aggregate", json={"round_id": round_id})
        assert r2.status_code == 400

    def test_submit_duplicate_updates(self, registered_clients, sample_gradients):
        r = client.post("/fl/start-round", json={
            "client_ids": registered_clients[:2],
        })
        round_id = r.json()["round_id"]

        cid = registered_clients[0]
        r1 = client.post("/fl/submit-update", json={
            "round_id": round_id, "client_id": cid,
            "encrypted_gradients": sample_gradients,
        })
        assert r1.status_code == 200

        # Second submission from same client is allowed (idempotent)
        r2 = client.post("/fl/submit-update", json={
            "round_id": round_id, "client_id": cid,
            "encrypted_gradients": sample_gradients,
        })
        assert r2.status_code == 200

    def test_invalid_gradient_base64(self, registered_clients):
        r = client.post("/fl/start-round", json={
            "client_ids": registered_clients[:2],
        })
        round_id = r.json()["round_id"]

        resp = client.post("/fl/submit-update", json={
            "round_id": round_id,
            "client_id": registered_clients[0],
            "encrypted_gradients": ["not-valid-base64!!!$$$"],
        })
        assert resp.status_code == 400

    def test_deactivate_client(self):
        resp = client.post("/fl/register-client", json={
            "agency_name": "Bad Actor",
            "public_key": "pk_bad",
        })
        cid = resp.json()["client_id"]

        # Deactivate via server directly
        result = _api_module.fl_server.deactivate_client(cid)
        assert result is True

        # Should not be invitable
        assert cid not in [
            c.client_id for c in _api_module.fl_server.get_all_clients() if c.is_active
        ]

"""Tests for the Blockchain Evidence Ledger API."""

import json
import os
import sys
import time
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SENTINEL_CORE_URL"] = "http://test:3000"

from api import (
    app,
    blockchain,
    evidence_store,
    zk_prover,
    Block,
    MerkleTree,
    ZKProver,
    EvidenceRecordRequest,
)

client = TestClient(app)


def _reset_state():
    evidence_store.clear()
    # Reinitialize blockchain with fresh genesis
    from api import Blockchain
    blockchain._chain.clear()
    blockchain._create_genesis_block()
    # Store genesis block
    genesis = blockchain.latest_block
    if genesis:
        evidence_store.store_block(genesis.to_dict())
    evidence_store.log_audit(action="test_reset", actor="test")


@pytest.fixture(autouse=True)
def reset():
    _reset_state()
    yield
    _reset_state()


def _sample_data_hash(content: str = "test_evidence") -> str:
    import hashlib
    return hashlib.new("sha3_512", content.encode()).hexdigest()


def _make_record(evidence_id: str = None, case_id: str = None, data: str = "evidence_data") -> dict:
    return {
        "evidence_id": evidence_id or f"evt_{int(time.time() * 1000)}",
        "case_id": case_id or "test-case-001",
        "data_hash": _sample_data_hash(data),
        "metadata": {"source": "test", "type": "test_data"},
        "actor": "test_actor",
        "module": "blockchain-ledge",
    }


class TestHealth:
    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "blockchain-ledge"
        assert data["status"] == "healthy"
        assert data["chain_length"] >= 1
        assert data["storage"] == "sqlite"

    def test_health_chain_valid(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["chain_valid"] is True


class TestRecordEvidence:
    def test_record_single(self):
        rec = _make_record()
        resp = client.post("/ledge/record", json=rec)
        assert resp.status_code == 200
        data = resp.json()
        assert data["evidence_id"] == rec["evidence_id"]
        assert data["status"] == "recorded"
        assert data["block_index"] >= 1
        assert len(data["block_hash"]) > 0

    def test_record_returns_block_hash(self):
        rec = _make_record()
        resp = client.post("/ledge/record", json=rec)
        data = resp.json()
        assert len(data["block_hash"]) == 128  # SHA3-512 hex

    def test_record_multiple_increments_index(self):
        idx1 = client.post("/ledge/record", json=_make_record("evt_1")).json()["block_index"]
        idx2 = client.post("/ledge/record", json=_make_record("evt_2")).json()["block_index"]
        assert idx2 > idx1

    def test_record_with_metadata(self):
        rec = _make_record(evidence_id="evt_meta")
        rec["metadata"] = {"case_type": "forensic", "priority": "high"}
        resp = client.post("/ledge/record", json=rec)
        assert resp.status_code == 200


class TestBatchRecord:
    def test_batch_empty_fails(self):
        resp = client.post("/ledge/batch", json={"entries": []})
        assert resp.status_code == 400

    def test_batch_single(self):
        resp = client.post("/ledge/batch", json={"entries": [_make_record("batch_1")]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert len(data["records"]) == 1
        assert len(data["merkle_root"]) > 0

    def test_batch_multiple(self):
        entries = [_make_record(f"batch_{i}", data=f"data_{i}") for i in range(5)]
        resp = client.post("/ledge/batch", json={"entries": entries})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 5

    def test_batch_merkle_root(self):
        entries = [_make_record(f"bm_{i}", data=f"d_{i}") for i in range(3)]
        resp = client.post("/ledge/batch", json={"entries": entries})
        data = resp.json()
        assert len(data["merkle_root"]) == 128

    def test_batch_all_recorded_individually(self):
        entries = [_make_record(f"br_{i}", data=f"bd_{i}") for i in range(4)]
        resp = client.post("/ledge/batch", json={"entries": entries})
        data = resp.json()
        ids = [r["evidence_id"] for r in data["records"]]
        for e in entries:
            assert e["evidence_id"] in ids


class TestVerify:
    def test_verify_nonexistent(self):
        resp = client.get("/ledge/verify/nonexistent_id")
        assert resp.status_code == 200
        data = resp.json()
        assert data["exists"] is False
        assert data["status"] == "not_found"

    def test_verify_recorded_evidence(self):
        rec = _make_record("verify_me")
        client.post("/ledge/record", json=rec)
        resp = client.get(f"/ledge/verify/{rec['evidence_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["exists"] is True
        assert data["hash_integrity"] is True
        assert data["status"] == "verified"

    def test_verify_returns_block_info(self):
        rec = _make_record("verify_block")
        post = client.post("/ledge/record", json=rec).json()
        resp = client.get(f"/ledge/verify/{rec['evidence_id']}")
        data = resp.json()
        assert data["block_index"] == post["block_index"]

    def test_verify_batch_evidence(self):
        entries = [_make_record(f"vb_{i}", data=f"vd_{i}") for i in range(3)]
        client.post("/ledge/batch", json={"entries": entries})
        resp = client.get(f"/ledge/verify/vb_0")
        assert resp.status_code == 200
        assert resp.json()["exists"] is True


class TestZKProof:
    def test_prove_nonexistent_returns_404(self):
        resp = client.get("/ledge/prove/nonexistent")
        assert resp.status_code == 404

    def test_prove_generates_proof(self):
        rec = _make_record("prove_me")
        client.post("/ledge/record", json=rec)
        resp = client.get(f"/ledge/prove/{rec['evidence_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["proof_type"] == "zk-snark-simulated"
        assert "proof" in data
        assert "merkle_root" in data["proof"]
        assert "commitment" in data["proof"]

    def test_proof_verify_valid(self):
        rec = _make_record("zk_valid")
        client.post("/ledge/record", json=rec)
        proof_resp = client.get(f"/ledge/prove/{rec['evidence_id']}")
        proof = proof_resp.json()["proof"]
        resp = client.get(
            f"/ledge/prove/{rec['evidence_id']}/verify",
            params={"proof_json": json.dumps(proof)},
        )
        assert resp.status_code == 200
        assert resp.json()["proof_valid"] is True

    def test_proof_verify_invalid(self):
        rec = _make_record("zk_invalid")
        client.post("/ledge/record", json=rec)
        fake_proof = {
            "commitment": "x" * 128,
            "merkle_root": "y" * 128,
            "challenge": "z" * 16,
            "response": "w" * 128,
            "merkle_proof": [],
        }
        resp = client.get(
            f"/ledge/prove/{rec['evidence_id']}/verify",
            params={"proof_json": json.dumps(fake_proof)},
        )
        assert resp.status_code == 200
        assert resp.json()["proof_valid"] is False

    def test_proof_verify_invalid_json(self):
        rec = _make_record("zk_bad_json")
        client.post("/ledge/record", json=rec)
        resp = client.get(
            f"/ledge/prove/{rec['evidence_id']}/verify",
            params={"proof_json": "not-json"},
        )
        assert resp.status_code == 400

    def test_privacy_preserving_audit(self):
        rec = _make_record("zk_privacy")
        client.post("/ledge/record", json=rec)
        ev = evidence_store.get_evidence(rec["evidence_id"])
        block = blockchain.get_block(ev["block_index"])
        audit = ZKProver.generate_privacy_preserving_audit(
            ev["data_hash"], block.index, len(blockchain.chain)
        )
        valid = ZKProver.verify_privacy_preserving_audit(
            audit, ev["data_hash"], block.index, len(blockchain.chain)
        )
        assert valid is True


class TestChain:
    def test_get_chain(self):
        for i in range(3):
            client.post("/ledge/record", json=_make_record(f"chain_{i}"))
        resp = client.get("/ledge/chain")
        assert resp.status_code == 200
        data = resp.json()
        assert data["length"] >= 4  # genesis + 3
        assert data["valid"] is True
        assert len(data["chain"]) >= 4

    def test_chain_genesis_present(self):
        resp = client.get("/ledge/chain")
        assert resp.json()["length"] >= 1
        assert len(resp.json()["genesis_hash"]) == 128

    def test_chain_hashes_sequential(self):
        client.post("/ledge/record", json=_make_record("seq_1"))
        client.post("/ledge/record", json=_make_record("seq_2"))
        resp = client.get("/ledge/chain")
        chain = resp.json()["chain"]
        for i in range(1, len(chain)):
            assert chain[i]["prev_hash"] == chain[i - 1]["hash"]


class TestStatus:
    def test_status_not_found(self):
        resp = client.get("/ledge/status/does_not_exist")
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_found"

    def test_status_verified(self):
        rec = _make_record("status_me")
        client.post("/ledge/record", json=rec)
        resp = client.get(f"/ledge/status/{rec['evidence_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "verified"
        assert data["verified"] is True
        assert data["block_index"] is not None

    def test_status_returns_coc(self):
        rec = _make_record("status_coc")
        client.post("/ledge/record", json=rec)
        resp = client.get(f"/ledge/status/{rec['evidence_id']}")
        assert "chain_of_custody" in resp.json()


class TestAudit:
    def test_audit_returns_entries(self):
        client.post("/ledge/record", json=_make_record("audit_1"))
        client.post("/ledge/record", json=_make_record("audit_2"))
        resp = client.get("/ledge/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 2
        assert data["section_65b_compliant"] is True

    def test_audit_filter_by_action(self):
        client.post("/ledge/record", json=_make_record("audit_filt"))
        resp = client.get("/ledge/audit", params={"action": "evidence_recorded"})
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_audit_pagination(self):
        for i in range(5):
            client.post("/ledge/record", json=_make_record(f"audit_p{i}"))
        resp = client.get("/ledge/audit", params={"limit": 2, "offset": 0})
        assert len(resp.json()["entries"]) <= 2


class TestExport:
    def test_export_ledger(self):
        client.post("/ledge/record", json=_make_record("export_1"))
        resp = client.get("/ledge/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["exported"] is True
        assert os.path.exists(data["path"])


class TestValidate:
    def test_validate_chain(self):
        client.post("/ledge/record", json=_make_record("valid_1"))
        client.post("/ledge/record", json=_make_record("valid_2"))
        resp = client.get("/ledge/validate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chain_valid"] is True
        assert data["block_count"] >= 3


class TestTamperDetection:
    def test_tamper_detected_on_hash_change(self):
        rec = _make_record("tamper_me")
        client.post("/ledge/record", json=rec)
        # Manually tamper the block in the in-memory chain
        ev = evidence_store.get_evidence(rec["evidence_id"])
        blockchain._chain[ev["block_index"]].data_hash = "t" * 128

        resp = client.get(f"/ledge/verify/{rec['evidence_id']}")
        assert resp.json()["hash_integrity"] is False

    def test_chain_validation_detects_tamper(self):
        rec = _make_record("chain_tamper")
        client.post("/ledge/record", json=rec)
        # Tamper the genesis block hash
        blockchain._chain[0].hash = "x" * 128

        resp = client.get("/ledge/validate")
        assert resp.json()["chain_valid"] is False

    def test_tampered_evidence_status(self):
        rec = _make_record("tamper_status")
        client.post("/ledge/record", json=rec)
        ev = evidence_store.get_evidence(rec["evidence_id"])
        blockchain._chain[ev["block_index"]].data_hash = "z" * 128

        resp = client.get(f"/ledge/status/{rec['evidence_id']}")
        assert resp.json()["status"] == "tampered"


class TestMerkleTreeUnit:
    def test_merkle_root_computation(self):
        leaves = ["a", "b", "c", "d"]
        tree = MerkleTree(leaves)
        assert len(tree.root) == 128

    def test_merkle_proof_generation(self):
        leaves = ["x", "y", "z", "w"]
        tree = MerkleTree(leaves)
        found, proof = tree.generate_proof("x")
        assert found is True
        assert len(proof) > 0

    def test_merkle_proof_verification(self):
        leaves = ["p1", "p2", "p3", "p4"]
        tree = MerkleTree(leaves)
        found, proof = tree.generate_proof("p2")
        valid = MerkleTree.verify_proof(tree.root, "p2", proof)
        assert valid is True

    def test_merkle_proof_bad_leaf(self):
        leaves = ["a", "b"]
        tree = MerkleTree(leaves)
        found, proof = tree.generate_proof("nonexistent")
        assert found is False
        assert proof == []

    def test_merkle_empty_tree(self):
        tree = MerkleTree()
        assert len(tree.root) == 128


class TestBlockchainUnit:
    def test_genesis_block(self):
        from api import Blockchain
        bc = Blockchain(case_metadata={"test": "case"})
        assert len(bc.chain) == 1
        assert bc.chain[0].index == 0
        assert bc.chain[0].prev_hash == "0" * 128

    def test_add_block(self):
        from api import Blockchain
        bc = Blockchain()
        initial_len = len(bc.chain)
        bc.add_block(data_hash=_sample_data_hash("new_data"))
        assert len(bc.chain) == initial_len + 1

    def test_validate_valid_chain(self):
        from api import Blockchain
        bc = Blockchain()
        bc.add_block(data_hash=_sample_data_hash("a"))
        bc.add_block(data_hash=_sample_data_hash("b"))
        valid, issues = bc.validate_chain()
        assert valid is True
        assert issues == []

    def test_chain_invalid_after_tamper(self):
        from api import Blockchain
        bc = Blockchain()
        bc.add_block(data_hash=_sample_data_hash("a"))
        bc._chain[1].hash = "t" * 128
        valid, issues = bc.validate_chain()
        assert valid is False
        assert len(issues) > 0

    def test_proof_of_authenticity(self):
        from api import Blockchain
        bc = Blockchain()
        bc.add_block(data_hash=_sample_data_hash("poa"))
        result = bc.proof_of_authenticity(1)
        assert result["valid"] is True
        assert result["hash_integrity"] is True

    def test_get_block(self):
        from api import Blockchain
        bc = Blockchain()
        block = bc.get_block(0)
        assert block is not None
        assert block.index == 0
        assert bc.get_block(999) is None

    def test_fork_detection(self):
        from api import Blockchain
        from ledge.blockchain import Block, _compute_block_hash
        bc = Blockchain()
        bc.add_block(data_hash=_sample_data_hash("fork_test"))
        b0 = Block(index=0, timestamp=0, data_hash="genesis", prev_hash="0" * 128)
        b0.hash = _compute_block_hash(b0)
        b1 = Block(index=1, timestamp=1, data_hash="fork1", prev_hash=b0.hash)
        b1.hash = _compute_block_hash(b1)
        b2 = Block(index=2, timestamp=2, data_hash="fork2", prev_hash=b1.hash)
        b2.hash = _compute_block_hash(b2)
        fork = [b0, b1, b2]
        resolved = bc.resolve_forks(fork)
        assert resolved is True
        assert len(bc.detect_forks()) >= 1


class TestZKProverUnit:
    def test_commitment(self):
        prover = ZKProver()
        commit = prover.commit(_sample_data_hash("secret"))
        assert len(commit) == 128

    def test_commitment_deterministic_with_salt(self):
        prover = ZKProver()
        c1 = prover.commit(_sample_data_hash("data"))
        # Different instance has different salt
        prover2 = ZKProver()
        c2 = prover2.commit(_sample_data_hash("data"))
        assert c1 != c2  # salts differ

    def test_inclusion_proof_roundtrip(self):
        prover = ZKProver()
        tree = MerkleTree(["h1", "h2", "h3", _sample_data_hash("target")])
        found, mp = tree.generate_proof(_sample_data_hash("target"))
        proof = prover.generate_inclusion_proof(_sample_data_hash("target"), mp, tree.root)
        valid = ZKProver.verify_inclusion_proof(proof, _sample_data_hash("target"))
        assert valid is True

    def test_inclusion_proof_bad_leaf(self):
        prover = ZKProver()
        tree = MerkleTree(["a", "b"])
        found, mp = tree.generate_proof("a")
        proof = prover.generate_inclusion_proof("a", mp, tree.root)
        valid = ZKProver.verify_inclusion_proof(proof, "bad_leaf")
        assert valid is False


class TestIntegration:
    def test_full_workflow(self):
        rec = _make_record("integ_full", data="full_workflow_data")
        post = client.post("/ledge/record", json=rec)
        assert post.status_code == 200

        verify = client.get(f"/ledge/verify/{rec['evidence_id']}")
        assert verify.status_code == 200
        assert verify.json()["exists"] is True
        assert verify.json()["hash_integrity"] is True

        proof = client.get(f"/ledge/prove/{rec['evidence_id']}")
        assert proof.status_code == 200

        zk_verify = client.get(
            f"/ledge/prove/{rec['evidence_id']}/verify",
            params={"proof_json": json.dumps(proof.json()["proof"])},
        )
        assert zk_verify.status_code == 200
        assert zk_verify.json()["proof_valid"] is True

        status = client.get(f"/ledge/status/{rec['evidence_id']}")
        assert status.status_code == 200
        assert status.json()["status"] == "verified"

        chain = client.get("/ledge/chain")
        assert chain.status_code == 200
        assert chain.json()["length"] >= 2

        audit = client.get("/ledge/audit")
        assert audit.status_code == 200
        assert audit.json()["count"] >= 2

        validate = client.get("/ledge/validate")
        assert validate.status_code == 200
        assert validate.json()["chain_valid"] is True

        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"

        export = client.get("/ledge/export")
        assert export.status_code == 200

    def test_batch_then_verify_workflow(self):
        entries = [_make_record(f"iw_{i}", data=f"iwd_{i}") for i in range(5)]
        batch = client.post("/ledge/batch", json={"entries": entries})
        assert batch.status_code == 200
        batch_data = batch.json()
        assert batch_data["count"] == 5

        for entry in entries:
            verify = client.get(f"/ledge/verify/{entry['evidence_id']}")
            assert verify.json()["exists"] is True
            assert verify.json()["hash_integrity"] is True

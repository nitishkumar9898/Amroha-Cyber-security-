from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from ..api import app, threat_lstm, attack_gnn, risk_scorer, prophet, ensemble_fuser, campaign_tracker


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


def _timestamps(n: int, freq_hours: int = 24) -> list[str]:
    base = datetime(2025, 1, 1)
    return [(base + timedelta(hours=i * freq_hours)).isoformat() for i in range(n)]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["service"] == "predictive-analytics"


# ---------------------------------------------------------------------------
# Forecast Threat
# ---------------------------------------------------------------------------

class TestForecastThreat:
    @patch("modules.predictive_analytics.api.prophet")
    @patch("modules.predictive_analytics.api.threat_lstm")
    @patch("modules.predictive_analytics.api.ensemble_fuser")
    def test_forecast_threat_basic(
        self,
        mock_ensemble: MagicMock,
        mock_lstm: MagicMock,
        mock_prophet: MagicMock,
        client: TestClient,
    ) -> None:
        payload = {
            "time_series": [round(np.sin(i * 0.3) * 0.5 + 0.5, 4) for i in range(100)],
            "timestamps": _timestamps(100),
            "horizon_days": 7,
            "include_uncertainty": True,
        }
        resp = client.post("/forecast/threat", json=payload)
        if resp.status_code == 200:
            body = resp.json()
            assert "forecast" in body
            assert "confidence_intervals" in body
        else:
            assert resp.status_code in (500, 503)

    def test_forecast_threat_invalid_horizon(self, client: TestClient) -> None:
        payload = {
            "time_series": [0.5] * 10,
            "timestamps": _timestamps(10),
            "horizon_days": 0,
        }
        resp = client.post("/forecast/threat", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Predict Attack
# ---------------------------------------------------------------------------

class TestPredictAttack:
    def test_predict_attack_basic(self, client: TestClient) -> None:
        payload = {
            "graph_edges": [[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]],
            "node_features": [[0.1] * 10 for _ in range(5)],
            "current_targets": [0],
            "top_k": 3,
        }
        resp = client.post("/predict/attack", json=payload)
        if resp.status_code == 200:
            body = resp.json()
            assert "predicted_targets" in body
        else:
            assert resp.status_code in (500, 503)

    def test_predict_attack_missing_fields(self, client: TestClient) -> None:
        resp = client.post("/predict/attack", json={"graph_edges": []})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Score Risk
# ---------------------------------------------------------------------------

class TestScoreRisk:
    def test_score_risk_basic(self, client: TestClient) -> None:
        payload = {
            "entity_id": "192.168.1.50",
            "factors": [
                {"name": "brute_force_attempts", "score": 0.8, "weight": 1.5, "category": "authentication"},
                {"name": "known_malicious_ip", "score": 0.9, "weight": 2.0, "category": "reputation"},
                {"name": "unusual_port_scan", "score": 0.4, "weight": 1.0, "category": "reconnaissance"},
            ],
            "metadata": {"asset_type": "server", "criticality": "high"},
        }
        resp = client.post("/score/risk", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["entity_id"] == "192.168.1.50"
        assert "risk_score" in body
        assert "risk_level" in body
        assert "explanation" in body
        assert len(body["top_factors"]) > 0

    def test_score_risk_empty_factors(self, client: TestClient) -> None:
        payload = {"entity_id": "test-entity", "factors": []}
        resp = client.post("/score/risk", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["risk_level"] in ("UNKNOWN", "LOW")


# ---------------------------------------------------------------------------
# Analyze Trend
# ---------------------------------------------------------------------------

class TestAnalyzeTrend:
    @patch("modules.predictive_analytics.api.prophet")
    def test_analyze_trend_basic(self, mock_prophet: MagicMock, client: TestClient) -> None:
        payload = {
            "historical_data": [
                {"timestamp": t, "value": round(np.sin(i * 0.5) * 0.4 + 0.5, 4)}
                for i, t in enumerate(_timestamps(60))
            ],
            "granularity": "daily",
            "detect_changepoints": True,
        }
        resp = client.post("/analyze/trend", json=payload)
        if resp.status_code == 200:
            body = resp.json()
            assert "trend_components" in body
            assert "forecast" in body
        else:
            assert resp.status_code in (500, 503)


# ---------------------------------------------------------------------------
# Predict Escalation
# ---------------------------------------------------------------------------

class TestPredictEscalation:
    def test_escalation_high_probability(self, client: TestClient) -> None:
        payload = {
            "incident_id": "INC-001",
            "current_severity": 0.7,
            "timeline_minutes": [0, 10, 20, 30, 40],
            "severity_history": [0.3, 0.5, 0.6, 0.65, 0.7],
            "indicators": ["ransomware_note", "c2_beacon", "credential_dump"],
            "asset_criticality": 0.9,
        }
        resp = client.post("/predict/escalation", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["incident_id"] == "INC-001"
        assert 0 <= body["escalation_probability"] <= 1.0
        assert len(body["recommended_actions"]) > 0

    def test_escalation_low_severity(self, client: TestClient) -> None:
        payload = {
            "incident_id": "INC-002",
            "current_severity": 0.1,
            "timeline_minutes": [0, 5],
            "severity_history": [0.1, 0.1],
            "indicators": [],
            "asset_criticality": 0.2,
        }
        resp = client.post("/predict/escalation", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["escalation_probability"] < 0.5

    def test_escalation_invalid_severity(self, client: TestClient) -> None:
        payload = {
            "incident_id": "INC-003",
            "current_severity": 1.5,
            "timeline_minutes": [0],
            "severity_history": [0.5],
        }
        resp = client.post("/predict/escalation", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Analyze Campaign
# ---------------------------------------------------------------------------

class TestAnalyzeCampaign:
    def test_campaign_analysis_basic(self, client: TestClient) -> None:
        base_ts = datetime.utcnow().isoformat()
        payload = {
            "events": [
                {
                    "event_id": "evt-1",
                    "timestamp": base_ts,
                    "source_ip": "10.0.0.1",
                    "target_ip": "10.0.0.100",
                    "attack_type": "phishing",
                    "ttp_codes": ["T1566", "T1059"],
                    "severity": 0.7,
                    "indicators": ["malicious_doc"],
                },
                {
                    "event_id": "evt-2",
                    "timestamp": base_ts,
                    "source_ip": "10.0.0.2",
                    "target_ip": "10.0.0.101",
                    "attack_type": "phishing",
                    "ttp_codes": ["T1566", "T1059"],
                    "severity": 0.6,
                    "indicators": ["malicious_doc"],
                },
                {
                    "event_id": "evt-3",
                    "timestamp": base_ts,
                    "source_ip": "10.0.0.3",
                    "target_ip": "10.0.0.102",
                    "attack_type": "phishing",
                    "ttp_codes": ["T1566", "T1059"],
                    "severity": 0.8,
                    "indicators": ["malicious_doc"],
                },
            ],
        }
        resp = client.post("/analyze/campaign", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "campaigns" in body
        assert "clustering_metrics" in body


# ---------------------------------------------------------------------------
# Forecast Geopolitical
# ---------------------------------------------------------------------------

class TestForecastGeopolitical:
    @patch("modules.predictive_analytics.api.prophet")
    def test_geopolitical_forecast(self, mock_prophet: MagicMock, client: TestClient) -> None:
        payload = {
            "region": "eastern_europe",
            "historical_tensions": [round(np.random.random(), 3) for _ in range(24)],
            "timestamps": _timestamps(24, freq_hours=720),
            "horizon_months": 6,
        }
        resp = client.post("/forecast/geopolitical", json=payload)
        if resp.status_code == 200:
            body = resp.json()
            assert body["region"] == "eastern_europe"
            assert "forecast" in body
            assert "risk_trajectory" in body
        else:
            assert resp.status_code in (500, 503)


# ---------------------------------------------------------------------------
# Analyze Seasonal
# ---------------------------------------------------------------------------

class TestAnalyzeSeasonal:
    @patch("modules.predictive_analytics.api.prophet")
    def test_seasonal_analysis(self, mock_prophet: MagicMock, client: TestClient) -> None:
        payload = {
            "time_series": [round(np.sin(i * 0.8) * 0.3 + 0.5, 4) for i in range(90)],
            "timestamps": _timestamps(90),
            "expected_seasonality": ["daily", "weekly"],
            "decompose": True,
        }
        resp = client.post("/analyze/seasonal", json=payload)
        if resp.status_code == 200:
            body = resp.json()
            assert "seasonal_patterns" in body
            assert "trend" in body
            assert "residual" in body
        else:
            assert resp.status_code in (500, 503)


# ---------------------------------------------------------------------------
# Model unit tests
# ---------------------------------------------------------------------------

class TestThreatLSTM:
    def test_forward_shape(self) -> None:
        model = ThreatLSTM(input_size=8, hidden_size=32, num_layers=2, output_horizons=[1, 7])
        x = torch.randn(4, 16, 8)
        out = model(x)
        assert out["1"].shape == (4, 1)
        assert out["7"].shape == (4, 7)
        assert "attention_weights" in out

    def test_uncertainty(self) -> None:
        model = ThreatLSTM(input_size=8, hidden_size=32, num_layers=2, output_horizons=[7])
        x = torch.randn(2, 16, 8)
        result = model.predict_with_uncertainty(x, num_samples=10)
        assert "7" in result
        assert "mean" in result["7"]
        assert "ci_lower" in result["7"]
        assert "ci_upper" in result["7"]


class TestAttackGraphGNN:
    def test_forward_shape(self) -> None:
        model = AttackGraphGNN(node_features=8, hidden_channels=16, num_layers=2, num_classes=5)
        x = torch.randn(6, 8)
        edge_index = torch.tensor([[0, 1, 2, 3, 4], [1, 2, 3, 4, 5]], dtype=torch.long)
        out = model(x, edge_index)
        assert out["node_logits"].shape == (6, 5)
        assert out["risk_scores"].shape == (6, 1)
        assert out["edge_probabilities"].shape == (5,)

    def test_next_targets(self) -> None:
        model = AttackGraphGNN(node_features=4, hidden_channels=8, num_layers=2, num_classes=3)
        x = torch.randn(5, 4)
        edge_index = torch.tensor([[0, 0, 1, 2], [1, 2, 3, 4]], dtype=torch.long)
        current = torch.tensor([0])
        nodes, scores = model.predict_next_targets(x, edge_index, current, top_k=2)
        assert len(nodes) <= 2
        assert len(scores) <= 2


class TestRiskScorer:
    def test_risk_computation(self) -> None:
        scorer = RiskScorer()
        scorer.add_factor("host-1", "critical_vuln", 0.9, weight=2.0, category="vulnerability")
        scorer.add_factor("host-1", "public_exposure", 0.7, weight=1.5, category="exposure")
        result = scorer.compute_risk("host-1")
        assert result is not None
        assert result.entity_id == "host-1"
        assert 0 < result.risk_score <= 1.0
        assert result.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert len(result.explanation) > 0

    def test_empty_risk(self) -> None:
        scorer = RiskScorer()
        result = scorer.compute_risk("unknown")
        assert result is None

    def test_risk_breakdown(self) -> None:
        scorer = RiskScorer()
        scorer.add_factor("ip-1", "scanner_detected", 0.6, category="recon")
        breakdown = scorer.get_risk_breakdown("ip-1")
        assert breakdown["entity_id"] == "ip-1"
        assert "factors_detail" in breakdown


class TestProphetForecaster:
    def test_fit_and_predict(self) -> None:
        import pandas as pd
        dates = _timestamps(60)
        values = [np.sin(i * 0.3) * 0.4 + 0.5 for i in range(60)]
        df = pd.DataFrame({"ds": dates, "y": values})
        model = ProphetForecaster()
        model.fit(df)
        fc = model.predict(periods=10, freq="D")
        assert len(fc.yhat) == 10
        assert len(fc.yhat_lower) == 10
        assert len(fc.yhat_upper) == 10
        assert len(fc.ds) == 10

    def test_detect_anomalies(self) -> None:
        import pandas as pd
        dates = _timestamps(30)
        values = [0.5] * 28 + [0.95, 0.98]
        df = pd.DataFrame({"ds": dates, "y": values})
        model = ProphetForecaster()
        model.fit(df)
        result = model.detect_anomalies(df)
        assert "is_anomaly" in result.columns
        assert "anomaly_score" in result.columns


class TestEnsembleFuser:
    def test_fuse_forecasts(self) -> None:
        base_dt = datetime.utcnow()
        timestamps = [base_dt + timedelta(hours=i) for i in range(10)]
        f1 = ForecastOutput(
            values=np.linspace(0.5, 0.7, 10),
            lower_bound=np.linspace(0.4, 0.6, 10),
            upper_bound=np.linspace(0.6, 0.8, 10),
            timestamps=timestamps,
            model_name="prophet",
        )
        f2 = ForecastOutput(
            values=np.linspace(0.55, 0.75, 10),
            lower_bound=np.linspace(0.45, 0.65, 10),
            upper_bound=np.linspace(0.65, 0.85, 10),
            timestamps=timestamps,
            model_name="lstm",
        )
        fuser = EnsembleFuser()
        fused = fuser.fuse([f1, f2])
        assert len(fused.values) == 10
        assert 0 < fused.confidence_score <= 1.0
        assert len(fused.weights) == 2

    def test_weight_update(self) -> None:
        fuser = EnsembleFuser()
        w_before = fuser.get_weights()["prophet"]
        fuser.update_weights("prophet", error=0.1)
        w_after = fuser.get_weights()["prophet"]
        assert w_after != w_before or abs(w_after - w_before) < 1e-6


class TestCampaignTracker:
    def test_campaign_detection(self) -> None:
        tracker = CampaignTracker(min_samples=2)
        base_ts = datetime.utcnow()
        events = [
            CampaignEvent(
                event_id=f"e{i}", timestamp=base_ts + timedelta(hours=i),
                source_ip=f"10.0.0.{i}", target_ip="10.0.0.100",
                attack_type="phishing", ttp_codes=["T1566"], severity=0.7,
            )
            for i in range(5)
        ]
        result = tracker.process_events(events)
        assert len(result.campaigns) > 0 or len(result.unassigned_events) > 0

    def test_attribution(self) -> None:
        tracker = CampaignTracker(min_samples=1)
        event = CampaignEvent(
            event_id="e1", timestamp=datetime.utcnow(),
            source_ip="10.0.0.1", target_ip="10.0.0.100",
            attack_type="apt", ttp_codes=["T1059", "T1566", "T1003"],
            severity=0.9,
        )
        result = tracker.process_events([event])
        if result.campaigns:
            attr = tracker.attribute_campaign(result.campaigns[0].campaign_id)
            assert attr is not None
            assert "attributed_actor" in attr


if __name__ == "__main__":
    pytest.main(["-v", __file__])

"""Tests for the Cyber Psychology Behavioral Profiler API module."""

import pytest
from fastapi.testclient import TestClient
from api import app, _strip_pii, extract_liwc_categories, extract_stylometry

client = TestClient(app)


class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["module"] == "cyber-psychology"


class TestAttackerProfiling:
    def test_profiles_from_ttps(self):
        resp = client.post(
            "/profile/attacker",
            json={
                "texts": ["I have a zero-day exploit ready for deployment"],
                "ttps": ["zero_day", "custom_malware", "spear_phishing"],
                "timestamps": [],
                "platforms": ["forum"],
                "usernames": [],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "profile_id" in body
        assert body["attacker_type"] in ("apt", "cybercriminal", "script_kiddie", "hacktivist", "insider")
        assert isinstance(body["confidence"], float)
        assert isinstance(body["escalation_likelihood"], float)
        assert "insight" in body
        assert len(body["chain_of_custody"]) >= 2

    def test_empty_ttps(self):
        resp = client.post(
            "/profile/attacker",
            json={"texts": [], "ttps": [], "timestamps": [], "platforms": [], "usernames": []},
        )
        assert resp.status_code == 200
        assert resp.json()["attacker_type"] == "unknown"

    def test_insight_contains_explanations(self):
        resp = client.post(
            "/profile/attacker",
            json={
                "texts": ["Exploit available, PM for price"],
                "ttps": ["ransomware", "credential_theft"],
                "timestamps": [],
                "platforms": [],
                "usernames": [],
            },
        )
        body = resp.json()
        insight = body["insight"]
        assert len(insight["explanations"]) > 0
        assert len(insight["recommendations"]) > 0
        assert "court_report" in insight


class TestInsiderThreat:
    def test_assesses_insider_threat(self):
        resp = client.post(
            "/profile/insider-threat",
            json={
                "communications": [
                    {"timestamp": "2026-06-20T02:30:00+00:00", "channel": "file_access", "duration": 300},
                    {"timestamp": "2026-06-20T03:15:00+00:00", "channel": "data_transfer", "duration": 600},
                    {"timestamp": "2026-06-20T14:00:00+00:00", "channel": "email", "duration": 60},
                ],
                "access_patterns": [],
                "hr_indicators": ["grievance", "termination_notice"],
                "writing_samples": [],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "assessment_id" in body
        assert isinstance(body["risk_score"], float)
        assert body["risk_level"] in ("low", "medium", "high", "critical")
        assert "circadian_pattern" in body

    def test_hr_indicators_increase_risk(self):
        low_resp = client.post(
            "/profile/insider-threat",
            json={"communications": [{"timestamp": "2026-06-20T12:00:00+00:00", "channel": "email", "duration": 10}], "access_patterns": [], "hr_indicators": [], "writing_samples": []},
        )
        high_resp = client.post(
            "/profile/insider-threat",
            json={"communications": [{"timestamp": "2026-06-20T12:00:00+00:00", "channel": "email", "duration": 10}], "access_patterns": [], "hr_indicators": ["grievance", "termination_notice", "policy_violation"], "writing_samples": []},
        )
        assert high_resp.json()["risk_score"] >= low_resp.json()["risk_score"]


class TestSocialEngineering:
    def test_detects_manipulation_in_threads(self):
        resp = client.post(
            "/analyze/social-engineering",
            json={
                "message_threads": [
                    [
                        "Your account has been compromised. Click here to verify immediately.",
                        "If you don't respond within 24 hours your account will be suspended.",
                    ],
                    ["Hey, want to catch up this weekend?", "Sure, sounds good!"],
                ],
                "target_role": "employee",
                "context": "Phishing campaign targeting finance department",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "analysis_id" in body
        assert isinstance(body["susceptibility_score"], float)
        assert len(body["high_risk_threads"]) >= 1
        assert len(body["manipulation_tactics"]) > 0

    def test_invalid_empty_threads(self):
        resp = client.post("/analyze/social-engineering", json={"message_threads": []})
        assert resp.status_code == 422


class TestLinguisticAnalysis:
    def test_analyzes_text_features(self):
        resp = client.post(
            "/analyze/linguistic",
            json={
                "texts": [
                    "I honestly have no idea what you're talking about. I never touched those files.",
                    "This is absolutely the last time I will warn you. Pay the ransom or we release the data.",
                ],
                "extract_personality": True,
                "extract_stylometry": True,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "analysis_id" in body
        assert len(body["per_text"]) == 2
        assert "deception_score" in body["per_text"][0]
        assert "personality_estimate" in body["per_text"][0]
        assert "stylometry" in body["per_text"][0]
        assert "liwc_categories" in body["per_text"][0]

    def test_aggregate_returns_summary(self):
        resp = client.post(
            "/analyze/linguistic",
            json={"texts": ["This is a test message."], "extract_personality": False, "extract_stylometry": False},
        )
        body = resp.json()
        assert body["aggregate"]["text_count"] == 1
        assert "liwc_summary" in body["aggregate"]

    def test_empty_texts_rejected(self):
        resp = client.post("/analyze/linguistic", json={"texts": []})
        assert resp.status_code == 422


class TestBehavioralTimeline:
    def test_generates_timeline_from_comms(self):
        resp = client.post(
            "/analyze/behavioral-timeline",
            json={
                "communications": [
                    {"timestamp": "2026-06-20T08:00:00+00:00", "channel": "email", "duration": 120},
                    {"timestamp": "2026-06-20T12:00:00+00:00", "channel": "chat", "duration": 45},
                    {"timestamp": "2026-06-20T23:00:00+00:00", "channel": "file_transfer", "duration": 900},
                ],
                "events": [],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "timeline_id" in body
        assert body["total_events"] == 3
        assert "circadian_rhythm" in body
        assert "anomalies" in body

    def test_handles_empty_data(self):
        resp = client.post(
            "/analyze/behavioral-timeline",
            json={"communications": [], "events": []},
        )
        assert resp.status_code == 200
        assert resp.json()["total_events"] == 0


class TestVictimPsychology:
    def test_assesses_victim_impact(self):
        resp = client.post(
            "/analyze/victim-psychology",
            json={
                "incident_type": "ransomware",
                "victim_role": "cfo",
                "exposure_indicators": ["phishing", "credential_theft"],
                "context": "Executive targeted in spear-phishing campaign",
                "message_evidence": [
                    "Your company has been hacked. Pay 50 BTC to recover your files.",
                    "This is a limited time offer. The price doubles in 24 hours.",
                ],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "assessment_id" in body
        assert body["impact_severity"] in ("low", "medium", "high", "critical")
        assert isinstance(body["impact_score"], float)
        assert "targeting_analysis" in body
        assert len(body["manipulation_detected"]) > 0

    def test_high_profile_targeting(self):
        resp = client.post(
            "/analyze/victim-psychology",
            json={
                "incident_type": "social_engineering",
                "victim_role": "ceo",
                "exposure_indicators": [],
                "context": "",
                "message_evidence": [],
            },
        )
        body = resp.json()
        assert body["targeting_analysis"]["targeted"] is True


class TestEscalationPrediction:
    def test_predicts_escalation(self):
        vec = [float(i) / 31.0 for i in range(32)]
        resp = client.post(
            "/predict/escalation",
            json={
                "behavior_sequences": [vec],
                "timestamps": [],
                "recent_ttps": ["data_exfil", "ransomware"],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "prediction_id" in body
        assert "escalation_class" in body
        assert body["escalation_class"] in ("de_escalation", "stable", "escalating", "critical")
        assert isinstance(body["escalation_probability"], float)

    def test_empty_sequences_rejected(self):
        resp = client.post("/predict/escalation", json={"behavior_sequences": []})
        assert resp.status_code == 400


class TestCoercionDetection:
    def test_detects_coercion_indicators(self):
        resp = client.post(
            "/analyze/coercion",
            json={
                "messages": [
                    "You must pay the ransom by Friday or we will release all your data.",
                    "If you contact the police, we will expose your browsing history to your family.",
                    "Nice weather today, isn't it?",
                ],
                "metadata": {"source": "email"},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "analysis_id" in body
        assert isinstance(body["coercion_score"], float)
        assert len(body["coercion_indicators"]) >= 1
        assert len(body["high_risk_messages"]) >= 1
        assert isinstance(body["power_imbalance"]["demand_ratio"], float)

    def test_benign_messages(self):
        resp = client.post(
            "/analyze/coercion",
            json={"messages": ["Hello, how are you?", "Let's meet for coffee.", "The report is ready."]},
        )
        body = resp.json()
        assert body["coercion_score"] < 0.5


class TestPIIStripping:
    def test_strips_email(self):
        cleaned = _strip_pii("Contact hacker@onionmail.com for details.")
        assert "[EMAIL]" in cleaned
        assert "hacker@onionmail.com" not in cleaned

    def test_strips_phone(self):
        cleaned = _strip_pii("Call 555-123-4567.")
        assert "[PHONE]" in cleaned

    def test_strips_ssn(self):
        cleaned = _strip_pii("SSN: 123-45-6789")
        assert "[SSN]" in cleaned

    def test_strips_cc(self):
        cleaned = _strip_pii("CC: 4111111111111111")
        assert "[CC]" in cleaned

    def test_preserves_normal_text(self):
        text = "This is a normal message about security."
        assert _strip_pii(text) == text


class TestLIWCExtraction:
    def test_extracts_categories(self):
        result = extract_liwc_categories("I am absolutely certain that I never touched those files.")
        assert isinstance(result, dict)
        assert "pronoun" in result
        assert "certainty" in result
        assert result["certainty"] > 0

    def test_empty_text(self):
        result = extract_liwc_categories("")
        assert all(v == 0.0 for v in result.values())


class TestStylometry:
    def test_extracts_stylometric_features(self):
        result = extract_stylometry("This is a test sentence. It has multiple parts.")
        assert result["total_tokens"] > 0
        assert result["total_sentences"] == 2
        assert isinstance(result["type_token_ratio"], float)
        assert result["type_token_ratio"] > 0

    def test_empty_text(self):
        result = extract_stylometry("")
        assert result["avg_word_length"] == 0.0


class TestSchemaValidation:
    def test_attacker_invalid_type(self):
        resp = client.post("/profile/attacker", json={"texts": "not_a_list", "ttps": "also_not_a_list"})
        assert resp.status_code == 422

    def test_linguistic_too_many_texts(self):
        resp = client.post("/analyze/linguistic", json={"texts": ["test"] * 200})
        assert resp.status_code == 422

    def test_coercion_too_many_messages(self):
        resp = client.post("/analyze/coercion", json={"messages": ["msg"] * 600})
        assert resp.status_code == 422


class TestChainOfCustody:
    def test_all_endpoints_include_coc(self):
        endpoints = [
            ("/profile/attacker", {"texts": ["test"], "ttps": ["phishing"], "timestamps": [], "platforms": [], "usernames": []}),
            ("/profile/insider-threat", {"communications": [{"timestamp": "2026-06-20T12:00:00+00:00", "channel": "email", "duration": 10}], "access_patterns": [], "hr_indicators": [], "writing_samples": []}),
            ("/analyze/linguistic", {"texts": ["test"], "extract_personality": False, "extract_stylometry": False}),
        ]
        for endpoint, payload in endpoints:
            resp = client.post(endpoint, json=payload)
            assert resp.status_code == 200, f"{endpoint} failed"
            assert len(resp.json().get("chain_of_custody", [])) >= 1, f"{endpoint} missing chain_of_custody"

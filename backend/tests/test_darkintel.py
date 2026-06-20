import pytest
import json
from backend.app.modules.darkweb import DarkwebIntelligence
from backend.app.zkp import zkp_signer
from backend.app.services.darkintel_service import darkintel_engine
from ai_layer.federated import FederatedLearningNode, global_aggregator

def test_darkweb_crawler_exploit():
    res = DarkwebIntelligence.crawl_onion_index("Windows zero-day exploit payload")
    assert len(res) == 1
    assert res[0]["category"] == "EXPLOIT_MARKET"
    assert res[0]["severity"] == "CRITICAL"
    assert "win32k.sys" in res[0]["body_content"]

def test_darkweb_crawler_credentials():
    res = DarkwebIntelligence.crawl_onion_index("government credentials leak db")
    assert len(res) == 1
    assert res[0]["category"] == "CREDENTIAL_LEAK"
    assert "email:hash:salt" in res[0]["body_content"]

def test_threat_actor_profiling_utc3():
    # Timestamps during Moscow working hours (e.g. 10:00 to 16:00 UTC)
    timestamps = [
        "2026-06-19 10:00:00",
        "2026-06-18 11:30:00",
        "2026-06-17 14:00:00"
    ]
    profile = DarkwebIntelligence.profile_threat_actor("Troll_Operator_99", timestamps)
    assert profile["estimated_timezone"] == "UTC+3 (Eastern Europe / Moscow)"
    assert profile["nighttime_activity_flag"] is False
    assert "monero_wallet" in profile["cryptocurrency_wallets"]

def test_threat_actor_profiling_utc8():
    # Timestamps indicating late night activity (e.g. UTC 02:00, which is working hours for UTC+8)
    timestamps = [
        "2026-06-19 02:00:00",
        "2026-06-18 01:15:00"
    ]
    profile = DarkwebIntelligence.profile_threat_actor("Shadow_Broker_China", timestamps)
    assert profile["estimated_timezone"] == "UTC+8 (East Asia)"
    assert profile["nighttime_activity_flag"] is True

def test_zkp_generation_and_verification():
    report = {"summary": "Critical threat profile detected", "incidents": 5}
    officer = "officer_kapoor"
    
    proof = zkp_signer.generate_proof(report, officer)
    assert proof["dpdp_compliant"] is True
    
    # Verification should succeed with correct credentials
    assert zkp_signer.verify_proof(proof, report, officer) is True
    
    # Verification should fail if report is tampered
    tampered_report = {"summary": "Critical threat profile detected", "incidents": 6}
    assert zkp_signer.verify_proof(proof, tampered_report, officer) is False
    
    # Verification should fail if officer_id is incorrect
    assert zkp_signer.verify_proof(proof, report, "wrong_officer") is False

def test_federated_node_differential_privacy():
    node = FederatedLearningNode("NIA_Edge_01")
    proof = {"dpdp_compliant": True, "quantum_signature": "zkp_v1_test"}
    update_str = node.generate_differential_privacy_update(proof)
    
    update = json.loads(update_str)
    assert update["agency"] == "NIA_Edge_01"
    assert update["payload_type"] == "ZKP_ENCRYPTED_TENSORS"
    assert update["zkp_proof"] == proof

def test_global_aggregator_secure_mpc():
    initial_version = global_aggregator.global_knowledge_base_version
    
    updates = [
        json.dumps({"weights_hash": "h1", "payload_type": "ZKP_ENCRYPTED_TENSORS"}),
        json.dumps({"weights_hash": "h2", "payload_type": "ZKP_ENCRYPTED_TENSORS"})
    ]
    
    new_version = global_aggregator.aggregate_updates(updates)
    assert new_version > initial_version

def test_darkintel_service_engine():
    res = darkintel_engine.perform_darkweb_investigation(
        query="zero-day vulnerabilities leaked",
        officer_id="officer_reddy",
        agency_name="NIA"
    )
    assert res["darkintel_service_version"] == "1.0.0"
    assert len(res["crawled_onion_results"]) > 0
    assert len(res["threat_actor_profiles"]) > 0
    assert res["proof_of_forensic_integrity"]["verified_legitimate"] is True
    assert res["federated_learning_update"]["agency"] == "NIA"

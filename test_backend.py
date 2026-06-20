"""
Integration Test Suite for CyberThreatForge Backend
Demonstrates REST API requests for authentication, scenario logging, and forensics audits.
"""

import unittest
import json
import os
import sys

# Append backend path to import main app
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'app'))

try:
    from fastapi.testclient import TestClient
    from main import app
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

class TestCyberThreatForgeFullStack(unittest.TestCase):
    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI or TestClient dependencies not installed in this environment.")
        self.client = TestClient(app)
        
        # Test Credentials
        self.test_user = {
            "username": "investigator_sharma_test",
            "password": "secure_password_101",
            "role": "investigator",
            "agency": "NIA-CYBER"
        }

    def test_auth_pipeline(self):
        # 1. Register User (idempotent)
        reg_resp = self.client.post("/api/auth/register", json=self.test_user)
        # Accept 200 (new) or 400 (already exists)
        self.assertIn(reg_resp.status_code, [200, 400])
        if reg_resp.status_code == 200:
            self.assertEqual(reg_resp.json()["username"], self.test_user["username"])

        # 2. Get Access Token
        tok_resp = self.client.post("/api/auth/token", json=self.test_user)
        self.assertEqual(tok_resp.status_code, 200)
        token = tok_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}

        # 3. Create Scenario Run
        scenario_data = {
            "scenario_id": "SCENARIO-2026-TEST",
            "name": "Integration Test Scenario",
            "threat_actor": "Mock-APT-Agent",
            "target_sector": "Aerospace Research"
        }
        scen_resp = self.client.post("/api/scenario/runs", json=scenario_data, headers=self.headers)
        self.assertEqual(scen_resp.status_code, 200)
        run_id = scen_resp.json()["id"]

        # 4. Trigger Phase Update
        phase_resp = self.client.post(f"/api/scenario/runs/{run_id}/phase?phase_name=Intrusion%20Log%20Generation", headers=self.headers)
        self.assertEqual(phase_resp.status_code, 200)
        self.assertIn("Intrusion Log Generation", phase_resp.json()["completed_phases"])

        # 5. Dynamic Module - Deepfake Analysis Check
        df_resp = self.client.get("/api/forensics/deepfake?filepath=evidence_video_fake.mp4", headers=self.headers)
        self.assertEqual(df_resp.status_code, 200)
        self.assertEqual(df_resp.json()["classification"], "MANIPULATED")

        # 6. Dynamic Module - Cyber Psychology Profiling
        psy_data = "Urgent response required immediately. Transfer payment keys to avoid data destruction."
        psy_resp = self.client.post(f"/api/forensics/psychology?text_sample={psy_data}", headers=self.headers)
        self.assertEqual(psy_resp.status_code, 200)
        self.assertEqual(psy_resp.json()["linguistic_metrics"]["urgency_markers"], "HIGH")

        print("\n[+] Integration Test execution successful: All core API routes functional.")

    def test_insureguard_flow(self):
        # 1. Create Policy
        policy_data = {
            "policy_number": "POL123",
            "insured_entity": "Acme Corp",
            "coverage_limit": 1000000,
            "premium": 5000
        }
        policy_resp = self.client.post("/api/insureguard/policy", json=policy_data, headers=self.headers)
        self.assertEqual(policy_resp.status_code, 200)
        policy_id = policy_resp.json()["id"]
        # 2. List Policies
        list_resp = self.client.get("/api/insureguard/policy", headers=self.headers)
        self.assertEqual(list_resp.status_code, 200)
        self.assertTrue(any(p["id"] == policy_id for p in list_resp.json()))
        # 3. Submit Claim
        claim_data = {
            "policy_id": policy_id,
            "incident_type": "Data Breach",
            "reported_loss": 200000
        }
        claim_resp = self.client.post("/api/insureguard/claim", json=claim_data, headers=self.headers)
        self.assertEqual(claim_resp.status_code, 200)
        # 4. Premium Recommendation
        prem_resp = self.client.get(f"/api/insureguard/policy/{policy_id}/premium-recommendation", headers=self.headers)
        self.assertEqual(prem_resp.status_code, 200)
        self.assertIn("recommended_premium", prem_resp.json())

    def test_batch1_modules(self):
        # ModelDefender
        md_resp = self.client.post("/api/modeldefender/watermark", json={"model_name": "Llama3-Core", "owner_id": "Gov-01"}, headers=self.headers)
        self.assertEqual(md_resp.status_code, 200)
        self.assertIn("watermark_hash", md_resp.json())

        # FirmwareGuard
        fg_data = {"device_model": "RTU-500", "version": "v2.1", "file_hash": "abcdbad", "is_signed": False}
        fg_resp = self.client.post("/api/firmwareguard/firmware", json=fg_data, headers=self.headers)
        self.assertEqual(fg_resp.status_code, 200)

        # PsyOpsForge
        po_data = {"target_demographic": "Elections-2026", "misinformation_type": "Deepfake Video"}
        po_resp = self.client.post("/api/psyopsforge/campaigns", json=po_data, headers=self.headers)
        self.assertEqual(po_resp.status_code, 200)

        # Correlix
        cx_data = {"source_module": "FirmwareGuard", "target_module": "PsyOpsForge"}
        cx_resp = self.client.post("/api/correlix/correlate", json=cx_data, headers=self.headers)
        self.assertEqual(cx_resp.status_code, 200)
        self.assertEqual(cx_resp.json()["status"], "Correlated")

    def test_batch2_modules(self):
        # CollabSpace
        cs_data = {"name": "Operation Titan", "owner": "Admin"}
        cs_resp = self.client.post("/api/collabspace/workspaces", json=cs_data, headers=self.headers)
        self.assertEqual(cs_resp.status_code, 200)
        self.assertIn("id", cs_resp.json())

        # LearnForge
        lf_data = {"incident_id": "INC-001", "raw_report_text": "Breach in sector 4"}
        lf_resp = self.client.post("/api/learnforge/extract", json=lf_data, headers=self.headers)
        self.assertEqual(lf_resp.status_code, 200)

        # Behavix
        bx_data = {"username": "Agent_007"}
        bx_resp = self.client.post("/api/behavix/profiles", json=bx_data, headers=self.headers)
        self.assertEqual(bx_resp.status_code, 200)

        # UndergroundForge
        ug_data = {"marketplace_url": "onion://market", "target_keyword": "0-day"}
        ug_resp = self.client.post("/api/undergroundforge/scan", json=ug_data, headers=self.headers)
        self.assertEqual(ug_resp.status_code, 200)

    def test_batch3_modules(self):
        # ZeroDayForge
        zd_data = {"software_component": "Linux Kernel", "version": "6.1.1"}
        zd_resp = self.client.post("/api/zerodayforge/predict", json=zd_data, headers=self.headers)
        self.assertEqual(zd_resp.status_code, 200)

        # LinguaGuard
        lg_data = {"source_language": "Russian", "original_text": "Attack grid tomorrow"}
        lg_resp = self.client.post("/api/linguaguard/translate", json=lg_data, headers=self.headers)
        self.assertEqual(lg_resp.status_code, 200)

        # AnomalyMaster
        am_data = {"metric_source": "CPU", "observed_value": 98.0, "expected_value": 30.0}
        am_resp = self.client.post("/api/anomalymaster/report", json=am_data, headers=self.headers)
        self.assertEqual(am_resp.status_code, 200)

        # VoiceGuard
        vg_data = {"audio_file_hash": "0x123abc", "speaker_id": "CEO_Fake"}
        vg_resp = self.client.post("/api/voiceguard/analyze", json=vg_data, headers=self.headers)
        self.assertEqual(vg_resp.status_code, 200)

    def test_batch4_modules(self):
        # SmartCityGuard
        sc_data = {"city_zone": "Downtown A", "iot_device_type": "Traffic Light", "device_id": "TL-001"}
        sc_resp = self.client.post("/api/smartcityguard/events", json=sc_data, headers=self.headers)
        self.assertEqual(sc_resp.status_code, 200)

        # DeFiGuard
        df_data = {"wallet_address": "0xTornadoCashProxy", "transaction_hash": "0xff"}
        df_resp = self.client.post("/api/defiguard/analyze", json=df_data, headers=self.headers)
        self.assertEqual(df_resp.status_code, 200)

        # AdversaryDefender
        ad_data = {"dataset_name": "TrainingData", "sample_id": "adv_img_1"}
        ad_resp = self.client.post("/api/adversarydefender/detect", json=ad_data, headers=self.headers)
        self.assertEqual(ad_resp.status_code, 200)

        # SovereignGuard
        sg_data = {"data_classification": "Top Secret", "destination_region": "CN-EAST"}
        sg_resp = self.client.post("/api/sovereignguard/check", json=sg_data, headers=self.headers)
        self.assertEqual(sg_resp.status_code, 200)

        # LegacyShield
        ls_data = {"system_type": "Siemens SCADA", "protocol": "Modbus/TCP", "air_gap_status": "Intact"}
        ls_resp = self.client.post("/api/legacyshield/investigate", json=ls_data, headers=self.headers)
        self.assertEqual(ls_resp.status_code, 200)

if __name__ == "__main__":
    unittest.main()

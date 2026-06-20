import pytest
import json
from app.modules.collabguard.zkp_auth import zkp_auth
from app.modules.collabguard.evidence_vault import evidence_vault
from app.modules.collabguard.joint_workflow import joint_workflow
from app.modules.collabguard.audit_ledger import audit_ledger
from app.modules.collabguard.compliance_exporter import compliance_exporter

@pytest.mark.asyncio
async def test_zkp_auth():
    res_valid = await zkp_auth.verify_proof("agency_A", "some_valid_zkp_payload")
    assert res_valid["access_granted"] is True
    
    res_invalid = await zkp_auth.verify_proof("agency_A", "invalid_payload")
    assert res_invalid["access_granted"] is False

@pytest.mark.asyncio
async def test_evidence_vault():
    ev_id = await evidence_vault.store_evidence("agency_A", {"file": "malware.exe"})
    assert ev_id is not None
    
    # Owner access
    res_owner = await evidence_vault.access_evidence("agency_A", ev_id)
    assert res_owner["status"] == "success"
    
    # Denied access
    res_denied = await evidence_vault.access_evidence("agency_B", ev_id)
    assert res_denied["status"] == "access_denied"
    
    # Grant and access
    await evidence_vault.grant_access("agency_A", ev_id, "agency_B")
    res_granted = await evidence_vault.access_evidence("agency_B", ev_id)
    assert res_granted["status"] == "success"

@pytest.mark.asyncio
async def test_joint_workflow():
    inv_id = await joint_workflow.create_investigation("FBI", "Operation Aurora")
    assert inv_id.startswith("inv_")
    
    await joint_workflow.add_participant(inv_id, "Interpol")
    assert "Interpol" in joint_workflow.investigations[inv_id]["participants"]
    
    await joint_workflow.add_note(inv_id, "FBI", "Found C2 server IP")
    assert len(joint_workflow.investigations[inv_id]["notes"]) == 1

@pytest.mark.asyncio
async def test_audit_ledger():
    await audit_ledger.append_log("agency_A", "TEST_ACTION", "resource_1")
    logs = await audit_ledger.get_logs()
    assert len(logs) > 0
    assert logs[-1]["action"] == "TEST_ACTION"

@pytest.mark.asyncio
async def test_compliance_exporter():
    raw_data = {"id": "test_1", "description": "test data"}
    stix_json = await compliance_exporter.export_stix_format(raw_data)
    stix_dict = json.loads(stix_json)
    assert stix_dict["type"] == "bundle"
    assert len(stix_dict["objects"]) == 1

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.collabguard import AuditEntry, EvidenceRecord, InvestigationState
from app.schemas.collabguard import ZKPAuthRequest, EvidenceStoreRequest, EvidenceAccessRequest, WorkflowCreateRequest, WorkflowAddNoteRequest

from app.modules.collabguard.zkp_auth import zkp_auth
from app.modules.collabguard.evidence_vault import evidence_vault
from app.modules.collabguard.joint_workflow import joint_workflow
from app.modules.collabguard.audit_ledger import audit_ledger
from app.modules.collabguard.compliance_exporter import compliance_exporter

router = APIRouter()

@router.post("/auth/verify")
async def verify_agency_zkp(request: ZKPAuthRequest, db: Session = Depends(get_db)):
    result = await zkp_auth.verify_proof(request.agency_id, request.zkp_payload)
    
    await audit_ledger.append_log(request.agency_id, "ZKP_AUTH", "auth_system", {"status": result["verification_status"]})
    db.add(AuditEntry(actor=request.agency_id, action="ZKP_AUTH", resource="auth_system", metadata_json={"status": result["verification_status"]}))
    db.commit()
    
    return result

@router.post("/evidence/store")
async def store_evidence(request: EvidenceStoreRequest, db: Session = Depends(get_db)):
    ev_id = await evidence_vault.store_evidence(request.agency_id, request.evidence_data)
    
    db_ev = EvidenceRecord(evidence_id=ev_id, owner=request.agency_id, data=request.evidence_data)
    db.add(db_ev)
    
    await audit_ledger.append_log(request.agency_id, "STORE_EVIDENCE", ev_id)
    db.add(AuditEntry(actor=request.agency_id, action="STORE_EVIDENCE", resource=ev_id))
    db.commit()
    
    return {"evidence_id": ev_id}

@router.post("/evidence/access")
async def access_evidence(request: EvidenceAccessRequest, db: Session = Depends(get_db)):
    result = await evidence_vault.access_evidence(request.requester_id, request.evidence_id)
    
    await audit_ledger.append_log(request.requester_id, "ACCESS_EVIDENCE", request.evidence_id, {"status": result["status"]})
    db.add(AuditEntry(actor=request.requester_id, action="ACCESS_EVIDENCE", resource=request.evidence_id, metadata_json={"status": result["status"]}))
    db.commit()
    
    if result["status"] != "success":
        raise HTTPException(status_code=403, detail="Access denied")
        
    return result

@router.post("/workflow/create")
async def create_workflow(request: WorkflowCreateRequest, db: Session = Depends(get_db)):
    inv_id = await joint_workflow.create_investigation(request.lead_agency, request.title)
    
    db_inv = InvestigationState(inv_id=inv_id, title=request.title, lead_agency=request.lead_agency, participants=[request.lead_agency])
    db.add(db_inv)
    
    await audit_ledger.append_log(request.lead_agency, "CREATE_INVESTIGATION", inv_id)
    db.add(AuditEntry(actor=request.lead_agency, action="CREATE_INVESTIGATION", resource=inv_id))
    db.commit()
    
    return {"investigation_id": inv_id}

@router.get("/compliance/export")
async def export_stix():
    # Example export of a mock bundle
    raw_data = {"id": "123", "description": "Mock export"}
    stix_json = await compliance_exporter.export_stix_format(raw_data)
    return {"stix_bundle": stix_json}

from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class ZKPAuthRequest(BaseModel):
    agency_id: str
    zkp_payload: str

class EvidenceStoreRequest(BaseModel):
    agency_id: str
    evidence_data: Dict[str, Any]

class EvidenceAccessRequest(BaseModel):
    requester_id: str
    evidence_id: str

class WorkflowCreateRequest(BaseModel):
    lead_agency: str
    title: str

class WorkflowAddNoteRequest(BaseModel):
    agency: str
    note: str

from pydantic import BaseModel, ConfigDict
from typing import Optional

class JurisdictionRequest(BaseModel):
    case_id: str
    source_country: str
    target_country: str

class JurisdictionResult(BaseModel):
    case_id: str
    primary_legal_framework: str
    jurisdiction_conflict: bool
    routing_advice: str

class EvidenceSharingRequest(BaseModel):
    evidence_id: str
    raw_data_string: str

class EvidenceSharingResult(BaseModel):
    evidence_id: str
    file_hash: str
    encryption_standard: str
    is_compliant: bool

class MLATRequest(BaseModel):
    requesting_country: str
    receiving_country: str

class MLATResult(BaseModel):
    treaty_status: str
    estimated_processing_days: int
    expedited_routing_available: bool

class AgencyLinkRequest(BaseModel):
    case_id: str
    agency_code: str

class AgencyLinkResult(BaseModel):
    status: str
    case_id: str
    agency_code: str

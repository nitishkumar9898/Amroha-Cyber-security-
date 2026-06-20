from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgencySessionBootstrapRequest(BaseModel):
    username: str
    agency: str
    role: str
    scopes: List[str] = Field(default_factory=list)
    clearance: str = "restricted"


class InvestigationCreateRequest(BaseModel):
    title: str
    objective: str
    lead_agency: str
    participating_agencies: List[str] = Field(default_factory=list)
    classification: str = "restricted"
    priority: str = "high"
    requested_modules: List[str] = Field(default_factory=list)
    jurisdictions: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)


class CorrelationRequest(BaseModel):
    case_id: Optional[str] = None
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    relation_keys: List[str] = Field(
        default_factory=lambda: [
            "indicator",
            "entity",
            "ip",
            "hash",
            "email",
            "wallet",
            "device",
            "location",
        ]
    )


class EvidenceShareRequest(BaseModel):
    case_id: str
    target_agencies: List[str] = Field(default_factory=list)
    evidence_payload: Dict[str, Any]
    legal_basis: str
    minimization_rules: List[str] = Field(default_factory=list)


class ReportRequest(BaseModel):
    case_id: str
    include_visuals: bool = True
    include_xai: bool = True
    format: str = "markdown"

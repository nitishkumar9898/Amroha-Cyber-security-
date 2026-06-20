from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# ── CSAM Hash Report ──────────────────────────────────────────────────

class CSAMHashReportCreate(BaseModel):
    hash_value: str = Field(..., description="Perceptual hash of the media (never raw content)")
    hash_algorithm: str = Field(default="phash", example="phash")
    source_platform: Optional[str] = None
    case_id: Optional[str] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class CSAMHashReportRead(BaseModel):
    id: int
    hash_value: str
    hash_algorithm: str
    match_confidence: float
    source_platform: Optional[str]
    reported_at: str
    status: str
    case_id: Optional[str]
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Grooming Analysis ─────────────────────────────────────────────────

class GroomingAnalysisCreate(BaseModel):
    conversation_hash: str = Field(..., description="Hash of the conversation text")
    platform: Optional[str] = None
    text_snippet: str = Field(..., description="Anonymised/redacted text for analysis")
    case_id: Optional[str] = None

class GroomingAnalysisRead(BaseModel):
    id: int
    conversation_hash: str
    platform: Optional[str]
    risk_score: float
    stage_detected: Optional[str]
    indicators: Optional[List[Dict[str, Any]]]
    analyzed_at: str
    case_id: Optional[str]

    class Config:
        from_attributes = True

# ── Dark Web Alert ────────────────────────────────────────────────────

class DarkWebAlertCreate(BaseModel):
    source: str = Field(..., example="tor_marketplace")
    url_hash: Optional[str] = None
    description: str
    severity: float = Field(default=0.0, ge=0.0, le=1.0)
    additional_metadata: Optional[Dict[str, Any]] = None

class DarkWebAlertRead(BaseModel):
    id: int
    source: str
    url_hash: Optional[str]
    description: str
    severity: float
    detected_at: str
    status: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Compliance Audit ──────────────────────────────────────────────────

class AuditLogRead(BaseModel):
    id: int
    action: str
    actor: str
    target_id: Optional[int]
    target_type: Optional[str]
    timestamp: str
    justification: Optional[str]
    details: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# ── Exfiltration Event ────────────────────────────────────────────────

class ExfiltrationEventCreate(BaseModel):
    event_type: str = Field(..., example="cloud_upload")
    actor_id: str = Field(..., example="EMP-4421")
    actor_type: str = Field(default="insider", example="insider")
    data_volume_mb: Optional[float] = None
    destination: Optional[str] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class ExfiltrationEventRead(BaseModel):
    id: int
    event_type: str
    actor_id: str
    actor_type: str
    risk_score: float
    data_volume_mb: Optional[float]
    destination: Optional[str]
    detected_at: str
    status: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Actor Correlation ─────────────────────────────────────────────────

class ActorCorrelationCreate(BaseModel):
    insider_id: str = Field(..., example="EMP-4421")
    external_id: str = Field(..., example="EXT-ACTOR-009")
    evidence_summary: Optional[str] = None
    indicators: Optional[List[Dict[str, Any]]] = None
    case_id: Optional[str] = None

class ActorCorrelationRead(BaseModel):
    id: int
    insider_id: str
    external_id: str
    correlation_score: float
    evidence_summary: Optional[str]
    indicators: Optional[List[Dict[str, Any]]]
    created_at: str
    case_id: Optional[str]

    class Config:
        from_attributes = True

# ── Trade Secret Simulation ──────────────────────────────────────────

class TradeSecretSimCreate(BaseModel):
    scenario_name: str = Field(..., example="mass_download_attempt")
    parameters: Dict[str, Any] = Field(..., description="Simulation configuration")

class TradeSecretSimRead(BaseModel):
    id: int
    scenario_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    protection_score: float
    created_at: str

    class Config:
        from_attributes = True

# ── IPShield Alert ───────────────────────────────────────────────────

class IPShieldAlertRead(BaseModel):
    id: int
    alert_type: str
    severity: float
    description: str
    related_event_ids: Optional[List[int]]
    related_correlation_ids: Optional[List[int]]
    created_at: str
    status: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

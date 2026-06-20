from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# ── IoMT Device ──────────────────────────────────────────────────────

class IoMTDeviceCreate(BaseModel):
    device_id: str = Field(..., example="PUMP-ICU-042")
    device_type: str = Field(..., example="infusion_pump")
    manufacturer: Optional[str] = None
    firmware_version: Optional[str] = None
    network_segment: Optional[str] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class IoMTDeviceRead(BaseModel):
    id: int
    device_id: str
    device_type: str
    manufacturer: Optional[str]
    firmware_version: Optional[str]
    risk_score: float
    vulnerabilities: Optional[List[Dict[str, Any]]]
    last_scanned: str
    network_segment: Optional[str]
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Health Data Breach ───────────────────────────────────────────────

class HealthDataBreachCreate(BaseModel):
    incident_id: str = Field(..., example="BREACH-2026-0087")
    affected_records: int = Field(default=0, ge=0)
    data_types_exposed: Optional[List[str]] = None
    attack_vector: Optional[str] = None
    source_ip: Optional[str] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class HealthDataBreachRead(BaseModel):
    id: int
    incident_id: str
    affected_records: int
    data_types_exposed: Optional[List[str]]
    attack_vector: Optional[str]
    source_ip: Optional[str]
    detected_at: str
    hipaa_violation: bool
    severity: float
    status: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Fake Medical Content ─────────────────────────────────────────────

class FakeMedicalContentCreate(BaseModel):
    content_type: str = Field(..., example="deepfake_doctor")
    source_url_hash: Optional[str] = None
    platform: Optional[str] = None
    claim_summary: Optional[str] = None
    text_content: str = Field(..., description="Text to analyse for fake medical claims")
    additional_metadata: Optional[Dict[str, Any]] = None

class FakeMedicalContentRead(BaseModel):
    id: int
    content_type: str
    source_url_hash: Optional[str]
    platform: Optional[str]
    confidence: float
    claim_summary: Optional[str]
    fact_check_result: Optional[str]
    detected_at: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Pandemic Misinformation ──────────────────────────────────────────

class PandemicMisinfoCreate(BaseModel):
    topic: str = Field(..., example="vaccine")
    narrative: str = Field(..., description="Summary of the misinformation narrative")
    spread_velocity: float = Field(default=0.0, ge=0.0)
    platforms_detected: Optional[List[str]] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class PandemicMisinfoRead(BaseModel):
    id: int
    topic: str
    narrative: str
    spread_velocity: float
    platforms_detected: Optional[List[str]]
    severity: float
    first_seen: str
    status: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

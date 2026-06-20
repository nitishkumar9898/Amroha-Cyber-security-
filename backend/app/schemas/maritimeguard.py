from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# ── AIS Signal ───────────────────────────────────────────────────────

class AISSignalCreate(BaseModel):
    mmsi: str = Field(..., example="211331640")
    vessel_name: Optional[str] = None
    latitude: float = Field(..., example=51.9485)
    longitude: float = Field(..., example=1.3530)
    speed_knots: Optional[float] = None
    course: Optional[float] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class AISSignalRead(BaseModel):
    id: int
    mmsi: str
    vessel_name: Optional[str]
    timestamp: str
    latitude: float
    longitude: float
    speed_knots: Optional[float]
    course: Optional[float]
    spoof_detected: bool
    spoof_confidence: float
    analysis: Optional[Dict[str, Any]]
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── AIS Batch (for multi-signal spoof detection) ─────────────────────

class AISBatchCreate(BaseModel):
    signals: List[AISSignalCreate]

# ── Shipboard Forensic ───────────────────────────────────────────────

class ShipboardForensicCreate(BaseModel):
    vessel_id: str = Field(..., example="IMO-9811000")
    system_type: str = Field(..., example="ECDIS")
    incident_type: Optional[str] = None
    findings: Optional[List[Dict[str, Any]]] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class ShipboardForensicRead(BaseModel):
    id: int
    vessel_id: str
    system_type: str
    incident_type: Optional[str]
    severity: float
    findings: Optional[List[Dict[str, Any]]]
    detected_at: str
    status: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Port Attack Simulation ──────────────────────────────────────────

class PortSimulationCreate(BaseModel):
    port_name: str = Field(..., example="Port of Rotterdam")
    scenario_name: str = Field(..., example="TOS ransomware")
    attack_vector: str = Field(..., example="TOS_compromise")
    parameters: Dict[str, Any] = Field(..., description="Simulation configuration")

class PortSimulationRead(BaseModel):
    id: int
    port_name: str
    scenario_name: str
    attack_vector: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    resilience_score: float
    created_at: str

    class Config:
        from_attributes = True

# ── Maritime Compliance ─────────────────────────────────────────────

class ComplianceCheckCreate(BaseModel):
    vessel_id: str = Field(..., example="IMO-9811000")
    framework: str = Field(..., example="IMO_MSC428")
    additional_metadata: Optional[Dict[str, Any]] = None

class ComplianceCheckRead(BaseModel):
    id: int
    vessel_id: str
    framework: str
    overall_score: float
    findings: Optional[List[Dict[str, Any]]]
    recommendations: Optional[List[Dict[str, Any]]]
    assessed_at: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

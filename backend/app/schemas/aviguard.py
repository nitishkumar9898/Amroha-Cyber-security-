from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# ── ADS-B Signal ─────────────────────────────────────────────────────

class ADSBSignalCreate(BaseModel):
    icao_hex: str = Field(..., example="A1B2C3")
    callsign: Optional[str] = None
    latitude: float = Field(..., example=28.5665)
    longitude: float = Field(..., example=77.1031)
    altitude_ft: Optional[float] = None
    speed_knots: Optional[float] = None
    heading: Optional[float] = None
    squawk: Optional[str] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class ADSBSignalRead(BaseModel):
    id: int
    icao_hex: str
    callsign: Optional[str]
    timestamp: str
    latitude: float
    longitude: float
    altitude_ft: Optional[float]
    speed_knots: Optional[float]
    heading: Optional[float]
    squawk: Optional[str]
    spoof_detected: bool
    spoof_confidence: float
    analysis: Optional[Dict[str, Any]]
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class ADSBBatchCreate(BaseModel):
    signals: List[ADSBSignalCreate]

# ── Avionics Forensic ────────────────────────────────────────────────

class AvionicsForensicCreate(BaseModel):
    aircraft_id: str = Field(..., example="VT-ABC")
    system_type: str = Field(..., example="FMS")
    incident_type: Optional[str] = None
    findings: Optional[List[Dict[str, Any]]] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class AvionicsForensicRead(BaseModel):
    id: int
    aircraft_id: str
    system_type: str
    incident_type: Optional[str]
    severity: float
    findings: Optional[List[Dict[str, Any]]]
    detected_at: str
    status: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Airport Network Scan ─────────────────────────────────────────────

class AirportScanCreate(BaseModel):
    airport_code: str = Field(..., example="DEL")
    scan_type: str = Field(default="network_segmentation", example="network_segmentation")
    additional_metadata: Optional[Dict[str, Any]] = None

class AirportScanRead(BaseModel):
    id: int
    airport_code: str
    scan_type: str
    risk_score: float
    findings: Optional[List[Dict[str, Any]]]
    scanned_at: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Drone Interference Simulation ───────────────────────────────────

class DroneSimCreate(BaseModel):
    scenario_name: str = Field(..., example="runway_swarm_incursion")
    attack_vector: str = Field(..., example="swarm_incursion")
    parameters: Dict[str, Any] = Field(..., description="Simulation configuration")

class DroneSimRead(BaseModel):
    id: int
    scenario_name: str
    attack_vector: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    resilience_score: float
    created_at: str

    class Config:
        from_attributes = True

# ── Aviation Compliance ──────────────────────────────────────────────

class AviationComplianceCreate(BaseModel):
    entity_id: str = Field(..., example="AI")
    entity_type: str = Field(default="airline", example="airline")
    framework: str = Field(..., example="ICAO_Annex17")
    additional_metadata: Optional[Dict[str, Any]] = None

class AviationComplianceRead(BaseModel):
    id: int
    entity_id: str
    entity_type: str
    framework: str
    overall_score: float
    findings: Optional[List[Dict[str, Any]]]
    recommendations: Optional[List[Dict[str, Any]]]
    assessed_at: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

from pydantic import BaseModel, ConfigDict
from typing import Optional

class TelemetryRequest(BaseModel):
    drone_id: str
    gps_lat: float
    gps_lon: float
    ins_lat: float
    ins_lon: float

class TelemetryResult(BaseModel):
    drone_id: str
    gps_variance_meters: float
    is_spoofed: bool
    action_taken: str

class MalwareAnalysisRequest(BaseModel):
    firmware_hash: str

class MalwareAnalysisResult(BaseModel):
    firmware_hash: str
    malware_family: str
    payload_extracted: bool

class SwarmSimulationRequest(BaseModel):
    swarm_id: str
    drone_count: int
    formation_type: str

class SwarmSimulationResult(BaseModel):
    swarm_id: str
    saturation_level: float
    threat_assessment: str

class EvidenceComplianceRequest(BaseModel):
    case_id: str
    file_name: str
    raw_data: str

class EvidenceComplianceResult(BaseModel):
    case_id: str
    file_name: str
    sha256_hash: str
    is_compliant: bool

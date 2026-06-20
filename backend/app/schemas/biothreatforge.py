from pydantic import BaseModel
from typing import Optional

class SequenceAnalysisRequest(BaseModel):
    sequence_id: str
    sequence_hash: str
    source_facility: str

class SequenceAnalysisResult(BaseModel):
    sequence_id: str
    bioweapon_probability: float
    pathogenic_markers_found: int
    is_threat: bool

class FacilityMonitorRequest(BaseModel):
    facility_id: str

class FacilityMonitorResult(BaseModel):
    facility_id: str
    scada_anomaly_score: float
    unauthorized_prints_detected: int
    is_compromised: bool

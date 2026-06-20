from pydantic import BaseModel, ConfigDict
from typing import Optional

class NeuralTelemetryRequest(BaseModel):
    subject_id: str
    alpha_band_hz: float
    beta_band_hz: float
    gamma_band_hz: float

class NeuralScanResult(BaseModel):
    subject_id: str
    is_anomalous: bool
    anomaly_type: Optional[str]
    status_message: str

class BCISimRequest(BaseModel):
    attack_vector: str

class BCISimResult(BaseModel):
    attack_vector: str
    biological_impact: str
    countermeasure_deployed: str

class PrivacyEnforcementRequest(BaseModel):
    data_packet_id: str
    raw_thought_data: str

class PrivacyEnforcementResult(BaseModel):
    data_packet_id: str
    is_secure: bool
    encryption_standard: str
    message: str

from pydantic import BaseModel, ConfigDict
from typing import Optional

class ScadaAnalysisRequest(BaseModel):
    device_id: str
    protocol: str
    packet_payload: str
    frequency_hz: float

class ScadaAnalysisResult(BaseModel):
    device_id: str
    is_anomalous: bool
    flag_reason: str

class PhysicalSimulationRequest(BaseModel):
    target_component: str
    injected_rpm: float
    normal_operating_rpm: float

class PhysicalSimulationResult(BaseModel):
    target_component: str
    kinetic_damage_probability: float
    structural_integrity_warning: str

class ResiliencePlanRequest(BaseModel):
    grid_sector: str
    current_load_mw: float
    compromised_nodes: int

class ResiliencePlanResult(BaseModel):
    grid_sector: str
    load_shedding_percentage: float
    islanding_required: bool
    action_plan: str

class ThreatForecastRequest(BaseModel):
    region: str
    iot_integration_level: float # 0.0 to 10.0
    past_incidents_count: int

class ThreatForecastResult(BaseModel):
    region: str
    five_year_risk_score: float
    primary_threat_vector: str

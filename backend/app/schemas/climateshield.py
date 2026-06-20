from pydantic import BaseModel, ConfigDict
from typing import Optional

class InfraAttackRequest(BaseModel):
    infrastructure_type: str
    weather_event: str
    cyber_attack_vector: str

class InfraAttackResult(BaseModel):
    infrastructure_type: str
    cascading_impact_score: float
    analysis_details: str

class ClimateSimRequest(BaseModel):
    manipulation_vector: str
    projected_years: int

class ClimateSimResult(BaseModel):
    manipulation_vector: str
    projected_years: int
    ecological_damage_index: float
    economic_impact_trillions: float
    details: str

class ResiliencePlanRequest(BaseModel):
    scenario_trigger: str
    severity_score: float

class ResiliencePlanResult(BaseModel):
    scenario_trigger: str
    recovery_strategy: str
    estimated_recovery_days: int

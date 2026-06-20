from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TechnologyProfileBase(BaseModel):
    tech_name: str
    sub_category: Optional[str] = None
    adoption_phase: str

class TechnologyProfileRead(TechnologyProfileBase):
    id: int
    last_updated: datetime

class RiskAssessmentRead(BaseModel):
    id: int
    tech_id: int
    cyber_risk_score: float
    physical_risk_score: float
    operational_risk_score: float
    composite_score: float
    assessment_date: datetime

class RiskScenarioRead(BaseModel):
    id: int
    assessment_id: int
    scenario_name: str
    description: str
    probability: float
    impact_level: str
    timeframe_years: int

class MitigationRoadmapRead(BaseModel):
    id: int
    scenario_id: int
    step_order: int
    action_item: str
    resource_requirement: str
    status: str

class AssessRequest(BaseModel):
    tech_name: str
    sub_category: str
    adoption_phase: str
    custom_parameters: dict = {}

class FullAssessmentResponse(BaseModel):
    profile: TechnologyProfileRead
    assessment: RiskAssessmentRead
    scenarios: List[RiskScenarioRead]
    roadmaps: List[MitigationRoadmapRead]

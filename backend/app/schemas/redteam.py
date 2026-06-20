from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class ScenarioBase(BaseModel):
    name: str
    description: str

class ScenarioCreate(ScenarioBase):
    pass

class ScenarioResponse(ScenarioBase):
    id: int
    attack_graph: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class SimulationStart(BaseModel):
    scenario_id: int

class SimulationStatusResponse(BaseModel):
    id: int
    scenario_id: int
    status: str
    metrics: Optional[Dict[str, Any]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ActionSubmit(BaseModel):
    team: str # 'blue' or 'red'
    action_type: str
    target: str

class AnalysisReportResponse(BaseModel):
    run_id: int
    status: str
    total_vulnerabilities_found: int
    recommendations: List[str]
    metrics: Dict[str, Any]

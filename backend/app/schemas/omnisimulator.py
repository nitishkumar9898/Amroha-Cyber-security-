from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class ScenarioCreateRequest(BaseModel):
    scenario_id: str
    name: str
    description: str

class ScenarioResult(BaseModel):
    scenario_id: str
    name: str
    status: str
    global_resilience_score: float

class EventTriggerRequest(BaseModel):
    scenario_id: str
    source_module: str
    event_description: str
    severity: str

class EventTriggerResult(BaseModel):
    event_id: str
    source_module: str
    event_description: str
    cascades_triggered: int
    new_resilience_score: float

class GlobalStateResponse(BaseModel):
    scenario_id: str
    status: str
    global_resilience_score: float
    total_events: int
    total_cascades: int

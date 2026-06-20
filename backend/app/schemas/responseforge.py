from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class ActionLogBase(BaseModel):
    action_type: str
    target: str
    status: str

class ActionLogOut(ActionLogBase):
    id: int
    incident_id: int
    executed_at: datetime
    
    class Config:
        from_attributes = True

class IncidentCreate(BaseModel):
    incident_type: str
    telemetry_data: Dict[str, Any]

class IncidentOut(BaseModel):
    id: int
    incident_type: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    telemetry_data: Dict[str, Any]
    root_cause: Optional[str] = None
    actions: List[ActionLogOut] = []
    
    class Config:
        from_attributes = True

class PlaybookRequest(BaseModel):
    incident_type: str
    context: Dict[str, Any]

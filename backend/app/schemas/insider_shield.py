from pydantic import ConfigDict
# backend/app/schemas/insider_shield.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class BehaviorIngestRequest(BaseModel):
    user_id: int
    feature_vector: List[float] = Field(..., description="Feature vector for baseline")
    timestamp: Optional[datetime] = None

class AccessEventIngestRequest(BaseModel):
    user_id: int
    resource: str
    action: str
    outcome: str
    timestamp: Optional[datetime] = None

class ExfiltrationEventIngestRequest(BaseModel):
    user_id: int
    data_size_bytes: int
    entropy: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class PsychProfileRequest(BaseModel):
    user_id: int
    profile_json: Dict[str, Any]
    timestamp: Optional[datetime] = None

class RiskScoreResponse(BaseModel):
    user_id: int
    score: float
    reason: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class AlertResponse(BaseModel):
    id: int
    user_id: int
    severity: str
    message: str
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime
    acknowledged: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Schema for DB models (responses)
class UserBehaviorBaselineSchema(BaseModel):
    id: int
    user_id: int
    feature_vector: List[float]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class AccessEventSchema(BaseModel):
    id: int
    user_id: int
    resource: str
    action: str
    outcome: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ExfiltrationEventSchema(BaseModel):
    id: int
    user_id: int
    data_size_bytes: int
    entropy: Optional[float]
    details: Optional[Dict[str, Any]]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class PsychProfileSchema(BaseModel):
    id: int
    user_id: int
    profile_json: Dict[str, Any]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class RiskScoreSchema(BaseModel):
    id: int
    user_id: int
    score: float
    reason: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class AlertSchema(BaseModel):
    id: int
    user_id: int
    severity: str
    message: str
    payload: Optional[Dict[str, Any]]
    created_at: datetime
    acknowledged: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


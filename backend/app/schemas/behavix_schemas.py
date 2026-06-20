from pydantic import BaseModel
from datetime import datetime

class BehaviorProfileCreate(BaseModel):
    username: str

class BehaviorProfileRead(BehaviorProfileCreate):
    id: int
    baseline_keystroke_dynamics: float
    baseline_mouse_patterns: float
    current_risk_score: float
    last_updated: datetime

    class Config:
        from_attributes = True

class SessionMetrics(BaseModel):
    username: str
    keystroke_speed: float
    mouse_jerkiness: float
    interaction_frequency: float

class AnomalyResult(BaseModel):
    username: str
    anomaly_detected: bool
    risk_score: float
    reason: str

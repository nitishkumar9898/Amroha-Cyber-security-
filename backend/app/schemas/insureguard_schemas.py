from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PolicyCreate(BaseModel):
    policy_number: str
    insured_entity: str
    coverage_limit: float
    premium: float

class PolicyRead(PolicyCreate):
    id: int
    created_at: datetime

class ClaimCreate(BaseModel):
    policy_id: int
    incident_type: str
    reported_loss: float

class ClaimRead(BaseModel):
    id: int
    policy_id: int
    incident_type: str
    reported_loss: float
    simulated_loss: Optional[float]
    status: str
    created_at: datetime

class RiskScore(BaseModel):
    cyber_risk: float
    financial_risk: float
    composite_score: float

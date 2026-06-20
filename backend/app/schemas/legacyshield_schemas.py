from pydantic import BaseModel
from datetime import datetime

class InvestigationRequest(BaseModel):
    system_type: str
    protocol: str
    air_gap_status: str

class InvestigationRead(InvestigationRequest):
    id: int
    migration_risk_score: float
    investigated_at: datetime

    class Config:
        from_attributes = True

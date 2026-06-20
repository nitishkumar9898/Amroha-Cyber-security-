from pydantic import BaseModel
from datetime import datetime

class SovereigntyCheckRequest(BaseModel):
    data_classification: str
    destination_region: str

class SovereigntyCheckRead(SovereigntyCheckRequest):
    id: int
    compliance_status: str
    violation_risk_score: float
    checked_at: datetime

    class Config:
        from_attributes = True

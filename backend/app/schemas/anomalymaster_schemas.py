from pydantic import BaseModel
from datetime import datetime

class AnomalyReport(BaseModel):
    metric_source: str
    observed_value: float
    expected_value: float

class AnomalyRead(AnomalyReport):
    id: int
    deviation_score: float
    root_cause_hypothesis: str
    detected_at: datetime

    class Config:
        from_attributes = True

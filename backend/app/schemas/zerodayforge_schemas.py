from pydantic import BaseModel
from datetime import datetime

class PredictionRequest(BaseModel):
    software_component: str
    version: str

class PredictionRead(BaseModel):
    id: int
    software_component: str
    version: str
    predicted_cve_severity: float
    vulnerability_type: str
    created_at: datetime

    class Config:
        from_attributes = True

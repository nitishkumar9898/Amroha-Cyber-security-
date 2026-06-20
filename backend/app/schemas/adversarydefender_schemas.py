from pydantic import BaseModel
from datetime import datetime

class DetectionRequest(BaseModel):
    dataset_name: str
    sample_id: str

class DetectionRead(DetectionRequest):
    id: int
    poison_probability: float
    perturbation_type: str
    detected_at: datetime

    class Config:
        from_attributes = True

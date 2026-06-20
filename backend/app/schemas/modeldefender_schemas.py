from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ModelDefenderLogCreate(BaseModel):
    model_name: str
    attack_type: str
    confidence_score: float
    defense_action: Optional[str] = "Monitored"

class ModelDefenderLogRead(ModelDefenderLogCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class WatermarkRequest(BaseModel):
    model_name: str
    owner_id: str

class WatermarkResponse(BaseModel):
    model_name: str
    watermark_hash: str
    status: str

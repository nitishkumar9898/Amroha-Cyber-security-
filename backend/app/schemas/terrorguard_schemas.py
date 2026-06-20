from pydantic import BaseModel
from datetime import datetime

class ThreatRequest(BaseModel):
    target_sector: str
    attack_vector: str

class ThreatRead(ThreatRequest):
    id: int
    state_sponsor_prob: float
    threat_level: str
    detected_at: datetime

    class Config:
        from_attributes = True

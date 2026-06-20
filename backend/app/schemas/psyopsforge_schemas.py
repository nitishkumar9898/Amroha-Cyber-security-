from pydantic import BaseModel
from datetime import datetime

class PsyOpsCampaignCreate(BaseModel):
    target_demographic: str
    misinformation_type: str

class PsyOpsCampaignRead(PsyOpsCampaignCreate):
    id: int
    sentiment_impact: float
    created_at: datetime
    status: str

    class Config:
        from_attributes = True

class CounterStrategyResponse(BaseModel):
    campaign_id: int
    strategy: str
    predicted_recovery: float

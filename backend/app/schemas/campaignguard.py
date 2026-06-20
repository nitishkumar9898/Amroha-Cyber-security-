from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DeepfakeCampaignBase(BaseModel):
    campaign_name: str
    target_entity: str
    payload_hash: str
    platforms_affected: List[str]

class DeepfakeCampaignRead(DeepfakeCampaignBase):
    id: int
    start_date: datetime

class BotNetworkNodeRead(BaseModel):
    id: int
    campaign_id: int
    node_id: str
    node_type: str
    platform: str
    engagement_score: float

class OpinionImpactRead(BaseModel):
    id: int
    campaign_id: int
    sentiment_drift: float
    reach_estimate: int
    impact_score: float
    analysis_date: datetime

class TakedownRecommendationRead(BaseModel):
    id: int
    campaign_id: int
    platform: str
    policy_violation: str
    evidence_summary: str
    status: str

class CampaignAnalyzeRequest(BaseModel):
    media_url: str
    target_entity: str

class CampaignAnalysisResponse(BaseModel):
    campaign: DeepfakeCampaignRead
    bot_nodes: List[BotNetworkNodeRead]
    impact: OpinionImpactRead
    recommendations: List[TakedownRecommendationRead]

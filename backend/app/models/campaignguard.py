from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
import datetime
from ..database import Base

class DeepfakeCampaign(Base):
    __tablename__ = "campaignguard_campaign"

    id = Column(Integer, primary_key=True, index=True)
    campaign_name = Column(String, index=True)
    target_entity = Column(String)
    payload_hash = Column(String, unique=True, index=True)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    platforms_affected = Column(JSON) # e.g. ["Twitter", "Telegram"]

class BotNetworkNode(Base):
    __tablename__ = "campaignguard_bot_node"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaignguard_campaign.id"))
    node_id = Column(String)
    node_type = Column(String) # "origin", "amplifier", "bridge"
    platform = Column(String)
    engagement_score = Column(Float)

class OpinionImpact(Base):
    __tablename__ = "campaignguard_impact"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaignguard_campaign.id"))
    sentiment_drift = Column(Float) # -1.0 to 1.0
    reach_estimate = Column(Integer)
    impact_score = Column(Float)
    analysis_date = Column(DateTime, default=datetime.datetime.utcnow)

class TakedownRecommendation(Base):
    __tablename__ = "campaignguard_takedown"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaignguard_campaign.id"))
    platform = Column(String)
    policy_violation = Column(String)
    evidence_summary = Column(String)
    status = Column(String, default="Draft") # Draft, Submitted, Resolved

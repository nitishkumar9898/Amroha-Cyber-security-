from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey
import datetime
from ..database import Base

class ThreatActor(Base):
    __tablename__ = "apthunter_threat_actor"

    id = Column(Integer, primary_key=True, index=True)
    actor_name = Column(String, unique=True, index=True)
    aliases = Column(JSON, nullable=True)
    origin_country = Column(String, nullable=True)
    target_sectors = Column(JSON, nullable=True)
    first_seen = Column(DateTime, nullable=True)

class APTCampaign(Base):
    __tablename__ = "apthunter_campaign"

    id = Column(Integer, primary_key=True, index=True)
    campaign_name = Column(String, index=True)
    threat_actor_id = Column(Integer, ForeignKey("apthunter_threat_actor.id"), nullable=True)
    attribution_confidence = Column(Float, default=0.0)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    additional_metadata = Column("metadata", JSON, nullable=True)

class TTPMapping(Base):
    __tablename__ = "apthunter_ttp_mapping"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("apthunter_campaign.id"))
    technique_id = Column(String, index=True)  # e.g., T1059
    technique_name = Column(String)
    graph_node_id = Column(String, nullable=True)  # ID in GNN simulation
    detection_score = Column(Float, default=0.0)

class PersistenceArtifact(Base):
    __tablename__ = "apthunter_persistence"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("apthunter_campaign.id"), nullable=True)
    artifact_type = Column(String, index=True) # e.g., registry, wmi, scheduled_task
    artifact_value = Column(String)
    stealth_score = Column(Float, default=0.0)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class PatentableIdea(Base):
    __tablename__ = "innovateguard_ideas"

    id = Column(Integer, primary_key=True, index=True)
    research_data_id = Column(String, index=True)
    detected_topic = Column(String)
    novelty_score = Column(Float)
    generated_claim = Column(String)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

class IPTheftInvestigation(Base):
    __tablename__ = "innovateguard_investigations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    data_volume_gb = Column(Float)
    time_of_access = Column(String) # Business vs Non-Business
    is_exfiltration_risk = Column(Boolean)
    action_taken = Column(String)
    investigated_at = Column(DateTime, default=datetime.datetime.utcnow)

class InnovationTrack(Base):
    __tablename__ = "innovateguard_tracks"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String)
    current_stage = Column(String) # RAW_RESEARCH -> PATENT_PENDING -> SECURED
    owner_id = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

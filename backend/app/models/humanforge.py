from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class PhishingAnalysis(Base):
    __tablename__ = "humanforge_phishing"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, index=True)
    is_phishing = Column(Boolean)
    confidence_score = Column(Float)
    detected_markers = Column(String)
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)

class PsychologicalManipulation(Base):
    __tablename__ = "humanforge_manipulation"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(String, index=True)
    manipulation_type = Column(String) # e.g., "AUTHORITY_IMPERSONATION"
    severity_level = Column(String)
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)

class AwarenessSimulation(Base):
    __tablename__ = "humanforge_simulation"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True)
    scenario_type = Column(String)
    payload_content = Column(String)
    difficulty_rating = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class InsiderThreatLink(Base):
    __tablename__ = "humanforge_insider_link"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True)
    base_insider_risk = Column(Float)
    adjusted_insider_risk = Column(Float)
    reasoning = Column(String)
    linked_at = Column(DateTime, default=datetime.datetime.utcnow)

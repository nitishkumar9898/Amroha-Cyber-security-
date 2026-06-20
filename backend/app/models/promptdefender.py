from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class PromptInjectionLog(Base):
    __tablename__ = "promptdefender_injection"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    original_prompt = Column(String)
    is_injection = Column(Boolean)
    threat_score = Column(Float)
    sanitized_prompt = Column(String)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

class HallucinationAnalysis(Base):
    __tablename__ = "promptdefender_hallucination"

    id = Column(Integer, primary_key=True, index=True)
    generated_text = Column(String)
    factual_consistency_score = Column(Float)
    is_hallucination = Column(Boolean)
    flag_reason = Column(String)
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)

class SyntheticContentForensics(Base):
    __tablename__ = "promptdefender_synthetic"

    id = Column(Integer, primary_key=True, index=True)
    text_sample = Column(String)
    perplexity_score = Column(Float)
    burstiness_score = Column(Float)
    is_ai_generated = Column(Boolean)
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)

class CrossModuleLink(Base):
    __tablename__ = "promptdefender_links"

    id = Column(Integer, primary_key=True, index=True)
    source_event_id = Column(String)
    target_module = Column(String) # e.g., "OSINT", "NeuroGuard"
    linked_at = Column(DateTime, default=datetime.datetime.utcnow)

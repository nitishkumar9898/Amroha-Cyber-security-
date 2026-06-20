# backend/app/models/osint.py

from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base

class SocialPost(Base):
    __tablename__ = "social_post"
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)
    post_id = Column(String(200), unique=True, nullable=False)
    content = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    author_hash = Column(String(64), nullable=False)  # hashed identifier for privacy
    url = Column(String(500), nullable=True)
    raw_json = Column(JSON, nullable=True)

class ActorProfile(Base):
    __tablename__ = "actor_profile"
    id = Column(Integer, primary_key=True, index=True)
    name_hash = Column(String(64), unique=True, nullable=False)
    platforms = Column(JSON, nullable=True)  # list of platforms where the actor appears
    affiliations = Column(JSON, nullable=True)
    risk_score = Column(Float, default=0.0)
    # optional relation to dark‑web indicators
    # darkweb_indicators = relationship("DarkWebIndicator", back_populates="actor")

class MisinformationEvent(Base):
    __tablename__ = "misinformation_event"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("social_post.id"), nullable=False)
    claim_text = Column(String(500), nullable=False)
    fact_check_url = Column(String(500), nullable=True)
    confidence = Column(Float, nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

class CrawlJob(Base):
    __tablename__ = "crawl_job"
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)
    query = Column(String(200), nullable=False)
    schedule = Column(String(100), nullable=True)  # cron‑like expression or "once"
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

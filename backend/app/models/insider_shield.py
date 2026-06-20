# backend/app/models/insider_shield.py

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Base is defined in backend/app/models/base.py (SQLAlchemy declarative base)
from .base import Base

class UserBehaviorBaseline(Base):
    __tablename__ = "user_behavior_baselines"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    feature_vector = Column(JSON, nullable=False)  # stored as list of floats
    timestamp = Column(DateTime, default=datetime.utcnow)

class AccessEvent(Base):
    __tablename__ = "access_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    resource = Column(String, nullable=False)
    action = Column(String, nullable=False)  # e.g., "read", "write", "delete"
    outcome = Column(String, nullable=False)  # e.g., "success", "denied"
    timestamp = Column(DateTime, default=datetime.utcnow)

class ExfiltrationEvent(Base):
    __tablename__ = "exfiltration_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    data_size_bytes = Column(Integer, nullable=False)
    entropy = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)

class PsychProfile(Base):
    __tablename__ = "psych_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True)
    profile_json = Column(JSON, nullable=False)  # output from psychology module
    timestamp = Column(DateTime, default=datetime.utcnow)

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    score = Column(Float, nullable=False)
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "insider_alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    severity = Column(String, nullable=False)  # e.g., "low", "medium", "high"
    message = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(DateTime, nullable=True)

# Relationships (optional for convenience)
UserBehaviorBaseline.__mapper_args__ = {"eager_defaults": True}
AccessEvent.__mapper_args__ = {"eager_defaults": True}
ExfiltrationEvent.__mapper_args__ = {"eager_defaults": True}
PsychProfile.__mapper_args__ = {"eager_defaults": True}
RiskScore.__mapper_args__ = {"eager_defaults": True}
Alert.__mapper_args__ = {"eager_defaults": True}

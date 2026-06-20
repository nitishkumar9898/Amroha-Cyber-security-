# backend/app/models/identity.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    biometric_templates = relationship("BiometricTemplate", back_populates="user", cascade="all, delete-orphan")
    verification_logs = relationship("VerificationLog", back_populates="user", cascade="all, delete-orphan")
    synthetic_alerts = relationship("SyntheticIdentityAlert", back_populates="user", cascade="all, delete-orphan")

class BiometricTemplate(Base):
    __tablename__ = "biometric_templates"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    modality = Column(String, nullable=False)  # "face", "voice", "fingerprint"
    template_blob = Column(LargeBinary, nullable=False)  # encrypted biometric template
    consent_given = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="biometric_templates")

class VerificationLog(Base):
    __tablename__ = "verification_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    modality = Column(String, nullable=False)
    result = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    anti_spoof_score = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    prev_hash = Column(String, nullable=True)
    curr_hash = Column(String, nullable=False)
    user = relationship("User", back_populates="verification_logs")

class SyntheticIdentityAlert(Base):
    __tablename__ = "synthetic_identity_alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="synthetic_alerts")

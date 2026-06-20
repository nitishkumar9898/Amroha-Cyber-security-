from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class VirtualAssetTransaction(Base):
    __tablename__ = "metaguard_assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String, index=True)
    wallet_hops = Column(Integer)
    time_window_seconds = Column(Float)
    is_laundering_risk = Column(Boolean)
    tracked_at = Column(DateTime, default=datetime.datetime.utcnow)

class AvatarBehavior(Base):
    __tablename__ = "metaguard_avatars"

    id = Column(Integer, primary_key=True, index=True)
    avatar_id = Column(String, index=True)
    kinematic_jitter = Column(Float)
    manipulative_language = Column(Boolean)
    social_engineering_risk = Column(Boolean)
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)

class CrimeCorrelation(Base):
    __tablename__ = "metaguard_correlations"

    id = Column(Integer, primary_key=True, index=True)
    virtual_incident_id = Column(String, index=True)
    hardware_id_hash = Column(String)
    physical_location_estimate = Column(String)
    correlated_at = Column(DateTime, default=datetime.datetime.utcnow)

class VirtualEvidence(Base):
    __tablename__ = "metaguard_evidence"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(String, index=True)
    manifest_url = Column(String)
    is_training_ready = Column(Boolean)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

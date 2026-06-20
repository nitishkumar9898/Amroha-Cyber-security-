from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class SatCommLog(Base):
    __tablename__ = "spaceguard_sat_comms"

    id = Column(Integer, primary_key=True, index=True)
    satellite_id = Column(String, index=True)
    protocol = Column(String)
    signal_to_noise_ratio = Column(Float)
    auth_handshake_valid = Column(Boolean)
    is_hijacked = Column(Boolean)
    logged_at = Column(DateTime, default=datetime.datetime.utcnow)

class OrbitalSupplyChainSim(Base):
    __tablename__ = "spaceguard_orbital_sims"

    id = Column(Integer, primary_key=True, index=True)
    mission_name = Column(String)
    payload_type = Column(String)
    firmware_hash = Column(String)
    orbital_risk_score = Column(Float) # 0.0 to 10.0
    vulnerability_found = Column(Boolean)
    simulated_at = Column(DateTime, default=datetime.datetime.utcnow)

class SpaceAssetStrategy(Base):
    __tablename__ = "spaceguard_asset_strategies"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String)
    threat_intel_level = Column(String) # LOW, ELEVATED, CRITICAL
    defensive_posture = Column(String)
    deployed_at = Column(DateTime, default=datetime.datetime.utcnow)

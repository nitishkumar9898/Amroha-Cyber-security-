from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class TelemetryAnalysis(Base):
    __tablename__ = "droneguard_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(String, index=True)
    gps_variance_meters = Column(Float)
    is_spoofed = Column(Boolean)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

class DroneMalware(Base):
    __tablename__ = "droneguard_malware"

    id = Column(Integer, primary_key=True, index=True)
    firmware_hash = Column(String, index=True)
    malware_family = Column(String)
    payload_extracted = Column(Boolean)
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)

class SwarmAttack(Base):
    __tablename__ = "droneguard_swarms"

    id = Column(Integer, primary_key=True, index=True)
    swarm_id = Column(String, index=True)
    drone_count = Column(Integer)
    formation_type = Column(String)
    saturation_level = Column(Float)
    simulated_at = Column(DateTime, default=datetime.datetime.utcnow)

class AerialEvidence(Base):
    __tablename__ = "droneguard_evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    file_name = Column(String)
    sha256_hash = Column(String)
    is_compliant = Column(Boolean)
    secured_at = Column(DateTime, default=datetime.datetime.utcnow)

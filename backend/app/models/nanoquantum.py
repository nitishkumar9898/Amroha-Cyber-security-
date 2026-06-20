from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class NanoDeviceScan(Base):
    __tablename__ = "nanoquantum_scans"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    electron_spin_variance = Column(Float)
    entanglement_stable = Column(Boolean)
    is_hijacked = Column(Boolean)
    scanned_at = Column(DateTime, default=datetime.datetime.utcnow)

class NanoThreatSim(Base):
    __tablename__ = "nanoquantum_sims"

    id = Column(Integer, primary_key=True, index=True)
    threat_type = Column(String) # GREY_GOO, NANOBOT_SWARM
    replication_rate = Column(Float) # Exponential factor
    material_consumed_kg = Column(Float)
    countermeasure_deployed = Column(String)
    simulated_at = Column(DateTime, default=datetime.datetime.utcnow)

class QuantumHardwareValidation(Base):
    __tablename__ = "nanoquantum_validations"

    id = Column(Integer, primary_key=True, index=True)
    hardware_id = Column(String)
    pqc_algorithm_applied = Column(String) # KYBER_1024, DILITHIUM
    atomic_integrity_verified = Column(Boolean)
    validated_at = Column(DateTime, default=datetime.datetime.utcnow)

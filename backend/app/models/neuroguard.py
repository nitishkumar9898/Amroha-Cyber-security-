from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class NeuralScan(Base):
    __tablename__ = "neuroguard_scans"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(String, index=True)
    alpha_band_hz = Column(Float)
    beta_band_hz = Column(Float)
    gamma_band_hz = Column(Float)
    is_anomalous = Column(Boolean)
    anomaly_type = Column(String, nullable=True) # SYNTHETIC_STIMULATION, CORTEX_HIJACK
    scanned_at = Column(DateTime, default=datetime.datetime.utcnow)

class BCIHackSimulation(Base):
    __tablename__ = "neuroguard_simulations"

    id = Column(Integer, primary_key=True, index=True)
    attack_vector = Column(String) # MEMORY_ALTERATION, MOTOR_HIJACK, NEURO_EAVESDROP
    biological_impact = Column(String)
    countermeasure_deployed = Column(String)
    simulated_at = Column(DateTime, default=datetime.datetime.utcnow)

class NeuralPrivacyLog(Base):
    __tablename__ = "neuroguard_privacy"

    id = Column(Integer, primary_key=True, index=True)
    data_packet_id = Column(String)
    encryption_standard = Column(String) # HOMOMORPHIC, LATTICE
    is_secure = Column(Boolean)
    enforced_at = Column(DateTime, default=datetime.datetime.utcnow)

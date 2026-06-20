from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class GenomicSequence(Base):
    __tablename__ = "biothreatforge_sequences"

    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(String, index=True, unique=True)
    sequence_hash = Column(String)
    source_facility = Column(String)
    intercepted_at = Column(DateTime, default=datetime.datetime.utcnow)

class SyntheticPathogenAnalysis(Base):
    __tablename__ = "biothreatforge_pathogen_analysis"

    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(String, index=True)
    bioweapon_probability = Column(Float)
    pathogenic_markers_found = Column(Integer)
    is_threat = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class BioFacilitySecurity(Base):
    __tablename__ = "biothreatforge_facilities"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(String, index=True)
    scada_anomaly_score = Column(Float)
    unauthorized_prints_detected = Column(Integer)
    is_compromised = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

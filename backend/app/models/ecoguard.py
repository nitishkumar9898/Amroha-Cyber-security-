from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, LargeBinary
import datetime
from ..database import Base

class WildlifeListing(Base):
    __tablename__ = "ecoguard_wildlife_listings"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, nullable=True)
    title = Column(String, index=True)
    description = Column(String)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    confidence = Column(Float, default=0.0)
    additional_metadata = Column("metadata", JSON, nullable=True)

class GPSForensic(Base):
    __tablename__ = "ecoguard_gps_forensics"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    raw_payload = Column(JSON)
    spoof_detected = Column(Boolean, default=False)
    analysis = Column(JSON, nullable=True)

class EnvDataRecord(Base):
    __tablename__ = "ecoguard_env_data"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    raw_data = Column(JSON)
    tamper_score = Column(Float, default=0.0)
    additional_metadata = Column("metadata", JSON, nullable=True)

class CollabRequest(Base):
    __tablename__ = "ecoguard_collab_requests"

    id = Column(Integer, primary_key=True, index=True)
    agency_name = Column(String, index=True)
    case_id = Column(String, index=True)
    request_payload = Column(JSON)
    status = Column(String, default="pending")  # pending, accepted, rejected, closed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

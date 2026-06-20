from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from datetime import datetime
from app.database import Base

class FirmwareImage(Base):
    __tablename__ = "hf_firmware_images"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    sha256 = Column(String, unique=True, index=True)
    size_bytes = Column(Integer)
    entropy = Column(Float)
    analysis_results = Column(JSON, default=dict)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class SideChannelTrace(Base):
    __tablename__ = "hf_side_channel_traces"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    trace_type = Column(String) # power, timing, em
    anomaly_score = Column(Float)
    is_attack = Column(Integer, default=0) # boolean as integer
    analyzed_at = Column(DateTime, default=datetime.utcnow)

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from ..database import Base

class FirmwareImage(Base):
    __tablename__ = "firmwareguard_images"
    id = Column(Integer, primary_key=True, index=True)
    device_model = Column(String, index=True)
    version = Column(String)
    file_hash = Column(String, unique=True)
    is_signed = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pending Analysis")

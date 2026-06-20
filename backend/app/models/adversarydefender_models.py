from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class PoisoningDetection(Base):
    __tablename__ = "adversarydefender_detections"
    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String)
    sample_id = Column(String)
    poison_probability = Column(Float, default=0.0)
    perturbation_type = Column(String)
    detected_at = Column(DateTime, default=datetime.utcnow)

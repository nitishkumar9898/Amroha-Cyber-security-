from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class VulnerabilityPrediction(Base):
    __tablename__ = "zerodayforge_predictions"
    id = Column(Integer, primary_key=True, index=True)
    software_component = Column(String, index=True)
    version = Column(String)
    predicted_cve_severity = Column(Float, default=0.0)
    vulnerability_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

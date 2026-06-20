from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class SystemAnomaly(Base):
    __tablename__ = "anomalymaster_anomalies"
    id = Column(Integer, primary_key=True, index=True)
    metric_source = Column(String)
    observed_value = Column(Float)
    expected_value = Column(Float)
    deviation_score = Column(Float, default=0.0)
    root_cause_hypothesis = Column(String)
    detected_at = Column(DateTime, default=datetime.utcnow)

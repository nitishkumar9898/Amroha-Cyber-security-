from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class CorrelationJob(Base):
    __tablename__ = "correlix_jobs"
    id = Column(Integer, primary_key=True, index=True)
    source_module = Column(String)
    target_module = Column(String)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pending")

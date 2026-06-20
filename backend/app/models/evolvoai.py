from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from datetime import datetime
from app.database import Base

class AIModelVersion(Base):
    __tablename__ = "ev_model_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, index=True)
    version = Column(String)
    status = Column(String, default="staged")
    metrics = Column(JSON, default=dict)
    registered_at = Column(DateTime, default=datetime.utcnow)

class HITLFeedback(Base):
    __tablename__ = "ev_hitl_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    data_id = Column(String, index=True)
    corrected_label = Column(String)
    analyst = Column(String)
    status = Column(String, default="pending_curation")
    submitted_at = Column(DateTime, default=datetime.utcnow)

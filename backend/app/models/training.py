from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, func
from datetime import datetime
from .database import Base

class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    scenario_name = Column(String, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, FAILED
    config = Column(JSON, nullable=True)

class TrainingResult(Base):
    __tablename__ = "training_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    details = Column(JSON, nullable=True)

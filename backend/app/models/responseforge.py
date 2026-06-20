from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Incident(Base):
    __tablename__ = "rf_incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String, index=True)
    status = Column(String, default="open") # open, investigating, contained, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    telemetry_data = Column(JSON, default=dict)
    root_cause = Column(String, nullable=True)
    
    actions = relationship("ActionLog", back_populates="incident")

class ActionLog(Base):
    __tablename__ = "rf_action_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("rf_incidents.id"))
    action_type = Column(String)
    target = Column(String)
    status = Column(String)
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    incident = relationship("Incident", back_populates="actions")

from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class PostIncidentLesson(Base):
    __tablename__ = "learnforge_lessons"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, index=True)
    extracted_knowledge = Column(String)
    relevance_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Extracted")

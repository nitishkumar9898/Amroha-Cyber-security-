from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class TranslationTask(Base):
    __tablename__ = "linguaguard_tasks"
    id = Column(Integer, primary_key=True, index=True)
    source_language = Column(String)
    original_text = Column(String)
    translated_text = Column(String)
    threat_intent_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

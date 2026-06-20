from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class ModelDefenderLog(Base):
    __tablename__ = "modeldefender_logs"
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    attack_type = Column(String) # e.g., "Extraction", "Evasion", "Poisoning"
    confidence_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    defense_action = Column(String, default="Monitored")

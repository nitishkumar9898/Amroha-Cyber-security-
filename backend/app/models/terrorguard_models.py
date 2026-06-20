from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class HybridWarfareThreat(Base):
    __tablename__ = "terrorguard_threats"
    id = Column(Integer, primary_key=True, index=True)
    target_sector = Column(String)
    attack_vector = Column(String)
    state_sponsor_prob = Column(Float, default=0.0)
    threat_level = Column(String)
    detected_at = Column(DateTime, default=datetime.utcnow)

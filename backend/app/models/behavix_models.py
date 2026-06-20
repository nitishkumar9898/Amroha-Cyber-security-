from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class BehaviorProfile(Base):
    __tablename__ = "behavix_profiles"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    baseline_keystroke_dynamics = Column(Float, default=1.0)
    baseline_mouse_patterns = Column(Float, default=1.0)
    current_risk_score = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

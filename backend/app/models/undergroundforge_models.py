from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class UndergroundAlert(Base):
    __tablename__ = "undergroundforge_alerts"
    id = Column(Integer, primary_key=True, index=True)
    marketplace = Column(String)
    keyword = Column(String)
    match_context = Column(String)
    threat_level = Column(Float, default=0.0)
    scraped_at = Column(DateTime, default=datetime.utcnow)

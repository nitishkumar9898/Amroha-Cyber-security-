from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class LegacyInvestigation(Base):
    __tablename__ = "legacyshield_investigations"
    id = Column(Integer, primary_key=True, index=True)
    system_type = Column(String)
    protocol = Column(String)
    air_gap_status = Column(String)
    migration_risk_score = Column(Float, default=0.0)
    investigated_at = Column(DateTime, default=datetime.utcnow)

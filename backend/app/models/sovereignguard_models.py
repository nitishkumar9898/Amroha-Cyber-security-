from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class DataSovereigntyCheck(Base):
    __tablename__ = "sovereignguard_checks"
    id = Column(Integer, primary_key=True, index=True)
    data_classification = Column(String)
    destination_region = Column(String)
    compliance_status = Column(String)
    violation_risk_score = Column(Float, default=0.0)
    checked_at = Column(DateTime, default=datetime.utcnow)

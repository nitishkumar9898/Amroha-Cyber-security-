from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class PsyOpsCampaign(Base):
    __tablename__ = "psyops_campaigns"
    id = Column(Integer, primary_key=True, index=True)
    target_demographic = Column(String)
    misinformation_type = Column(String)
    sentiment_impact = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Simulating")

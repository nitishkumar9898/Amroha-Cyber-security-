from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
import datetime
from ..database import Base

class Policy(Base):
    __tablename__ = "insureguard_policy"
    id = Column(Integer, primary_key=True, index=True)
    policy_number = Column(String, unique=True, index=True)
    insured_entity = Column(String)
    coverage_limit = Column(Float)
    premium = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Claim(Base):
    __tablename__ = "insureguard_claim"
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("insureguard_policy.id"))
    incident_type = Column(String)
    reported_loss = Column(Float)
    simulated_loss = Column(Float, nullable=True)
    status = Column(String, default="Submitted")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

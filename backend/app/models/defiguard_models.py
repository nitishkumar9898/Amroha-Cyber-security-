from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class DeFiTransaction(Base):
    __tablename__ = "defiguard_transactions"
    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String, index=True)
    transaction_hash = Column(String, unique=True, index=True)
    risk_score = Column(Float, default=0.0)
    flags = Column(String)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

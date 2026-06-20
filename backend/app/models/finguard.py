from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class TransactionAnomaly(Base):
    __tablename__ = "finguard_anomalies"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True)
    amount = Column(Float)
    velocity_score = Column(Float)
    is_anomalous = Column(Boolean)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

class PaymentTrace(Base):
    __tablename__ = "finguard_traces"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True)
    hop_count = Column(Integer)
    crosses_borders = Column(Boolean)
    complexity_score = Column(Float)
    traced_at = Column(DateTime, default=datetime.datetime.utcnow)

class LaunderingPattern(Base):
    __tablename__ = "finguard_laundering"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String, index=True)
    pattern_type = Column(String) # e.g., "SMURFING", "TUMBLING"
    osint_flagged = Column(Boolean)
    ransomware_linked = Column(Boolean)
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)

class ComplianceReport(Base):
    __tablename__ = "finguard_compliance"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String, index=True)
    agency = Column(String) # e.g., "RBI", "FIU-IND"
    report_hash = Column(String)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime

from ..database import Base

class RansomwareIncident(Base):
    __tablename__ = "ransomware_incidents"

    id = Column(Integer, primary_key=True, index=True)
    target_entity = Column(String, index=True)
    reported_at = Column(DateTime, default=datetime.datetime.utcnow)
    ransom_note = Column(String)
    demanded_amount = Column(Float)
    currency = Column(String, default="BTC")
    status = Column(String, default="OPEN") # OPEN, TRACING, CLOSED

class CryptoWallet(Base):
    __tablename__ = "crypto_wallets"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("ransomware_incidents.id"))
    address = Column(String, index=True)
    wallet_type = Column(String) # e.g., "INITIAL_DEPOSIT", "MIXER", "CASH_OUT"
    balance = Column(Float, default=0.0)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)

class TransactionTrace(Base):
    __tablename__ = "transaction_traces"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("ransomware_incidents.id"))
    from_address = Column(String)
    to_address = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    risk_score = Column(Float) # AI calculated likelihood of illicit activity

class ForensicEvidence(Base):
    __tablename__ = "forensic_evidences"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("ransomware_incidents.id"))
    evidence_type = Column(String) # e.g., "CHAIN_OF_CUSTODY", "HASH_LOG"
    data = Column(JSON)
    digital_signature = Column(String) # Simulated hash for compliance
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

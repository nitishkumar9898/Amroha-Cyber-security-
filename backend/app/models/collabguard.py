from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from app.database import Base

class AuditEntry(Base):
    __tablename__ = "cg_audit_ledger"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    actor = Column(String, index=True)
    action = Column(String)
    resource = Column(String)
    metadata_json = Column(JSON, default=dict)

class EvidenceRecord(Base):
    __tablename__ = "cg_evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String, index=True, unique=True)
    owner = Column(String, index=True)
    data = Column(JSON, default=dict)
    shared_with = Column(JSON, default=list)

class InvestigationState(Base):
    __tablename__ = "cg_investigations"
    
    id = Column(Integer, primary_key=True, index=True)
    inv_id = Column(String, index=True, unique=True)
    title = Column(String)
    lead_agency = Column(String)
    participants = Column(JSON, default=list)
    status = Column(String, default="open")
    notes = Column(JSON, default=list)

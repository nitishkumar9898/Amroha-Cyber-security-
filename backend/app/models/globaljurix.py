from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class JurisdictionMap(Base):
    __tablename__ = "globaljurix_jurisdiction"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    source_country = Column(String)
    target_country = Column(String)
    primary_legal_framework = Column(String)
    jurisdiction_conflict = Column(Boolean)
    mapped_at = Column(DateTime, default=datetime.datetime.utcnow)

class EvidenceProtocol(Base):
    __tablename__ = "globaljurix_evidence"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String, index=True)
    file_hash = Column(String)
    encryption_standard = Column(String)
    is_compliant = Column(Boolean)
    packaged_at = Column(DateTime, default=datetime.datetime.utcnow)

class MLATCompliance(Base):
    __tablename__ = "globaljurix_mlat"

    id = Column(Integer, primary_key=True, index=True)
    requesting_country = Column(String)
    receiving_country = Column(String)
    treaty_status = Column(String)
    estimated_processing_days = Column(Integer)
    checked_at = Column(DateTime, default=datetime.datetime.utcnow)

class AgencyCollaborationLink(Base):
    __tablename__ = "globaljurix_collab_links"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    agency_code = Column(String)
    link_status = Column(String)
    linked_at = Column(DateTime, default=datetime.datetime.utcnow)

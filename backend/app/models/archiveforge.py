from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, JSON
import datetime
from ..database import Base

class EvidenceRecord(Base):
    __tablename__ = "archiveforge_evidence"

    id = Column(Integer, primary_key=True, index=True)
    evidence_type = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    additional_metadata = Column("metadata", JSON, nullable=True)
    encrypted_blob = Column(LargeBinary, nullable=False)

class RetentionPolicy(Base):
    __tablename__ = "archiveforge_retention_policy"

    id = Column(Integer, primary_key=True, index=True)
    evidence_type = Column(String, unique=True, index=True)
    retention_days = Column(Integer, nullable=False)

class MigrationLog(Base):
    __tablename__ = "archiveforge_migration_log"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, index=True)
    from_format = Column(String)
    to_format = Column(String)
    migrated_at = Column(DateTime, default=datetime.datetime.utcnow)

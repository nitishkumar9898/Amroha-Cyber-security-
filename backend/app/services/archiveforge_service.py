from sqlalchemy.orm import Session
from ..models.archiveforge import EvidenceRecord, RetentionPolicy, MigrationLog
from ..schemas.archiveforge import EvidenceCreate
from ..modules.archiveforge_engine import encrypt_blob, decrypt_blob, migrate_format, index_evidence, search_evidence, is_expired
from datetime import datetime, timedelta
import json

def store_evidence(db: Session, payload: EvidenceCreate) -> EvidenceRecord:
    # Determine retention period from policy if exists
    policy = db.query(RetentionPolicy).filter(RetentionPolicy.evidence_type == payload.evidence_type).first()
    expires_at = None
    if policy:
        expires_at = datetime.utcnow() + timedelta(days=policy.retention_days)
    encrypted = encrypt_blob(payload.raw_data)
    record = EvidenceRecord(
        evidence_type=payload.evidence_type,
        additional_metadata=payload.additional_metadata,
        encrypted_blob=encrypted,
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    # Index for search
    index_evidence(record)
    return record

def retrieve_evidence(db: Session, record_id: int) -> dict:
    rec = db.query(EvidenceRecord).filter(EvidenceRecord.id == record_id).first()
    if not rec:
        raise ValueError("EvidenceRecord not found")
    raw = decrypt_blob(rec.encrypted_blob)
    return {
        "id": rec.id,
        "evidence_type": rec.evidence_type,
        "created_at": rec.created_at.isoformat(),
        "expires_at": rec.expires_at.isoformat() if rec.expires_at else None,
        "additional_metadata": rec.additional_metadata,
        "raw_data": raw,
    }

def run_migration(db: Session, record_id: int, target_format: str) -> MigrationLog:
    rec = db.query(EvidenceRecord).filter(EvidenceRecord.id == record_id).first()
    if not rec:
        raise ValueError("EvidenceRecord not found")
    mig_info = migrate_format(rec, target_format)
    # Update metadata with new format
    rec.additional_metadata = mig_info["metadata"]
    db.add(rec)
    log = MigrationLog(
        record_id=rec.id,
        from_format=mig_info["from_format"],
        to_format=mig_info["to_format"],
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def search_evidence_records(db: Session, query: str, top_k: int = 10):
    ids = search_evidence(query, top_k)
    if not ids:
        return []
    records = db.query(EvidenceRecord).filter(EvidenceRecord.id.in_(ids)).all()
    return records

def apply_retention_cleanup(db: Session) -> int:
    expired = db.query(EvidenceRecord).filter(EvidenceRecord.expires_at != None, EvidenceRecord.expires_at < datetime.utcnow()).all()
    count = len(expired)
    for rec in expired:
        db.delete(rec)
    db.commit()
    return count

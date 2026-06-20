from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import dependencies
from ..schemas.archiveforge import EvidenceCreate, EvidenceRead, RetentionPolicyRead, MigrationLogRead
from ..services.archiveforge_service import (
    store_evidence,
    retrieve_evidence,
    run_migration,
    search_evidence_records,
    apply_retention_cleanup,
)

router = APIRouter()

@router.post("/evidence", response_model=EvidenceRead)
def upload_evidence(payload: EvidenceCreate, db: Session = Depends(dependencies.get_db)):
    rec = store_evidence(db, payload)
    return EvidenceRead(
        id=rec.id,
        evidence_type=rec.evidence_type,
        created_at=rec.created_at.isoformat(),
        expires_at=rec.expires_at.isoformat() if rec.expires_at else None,
        metadata=rec.metadata,
    )

@router.get("/evidence/{record_id}")
def get_evidence(record_id: int, db: Session = Depends(dependencies.get_db)):
    return retrieve_evidence(db, record_id)

@router.post("/migrate/{record_id}")
def migrate_evidence(record_id: int, target_format: str, db: Session = Depends(dependencies.get_db)):
    log = run_migration(db, record_id, target_format)
    return MigrationLogRead(
        id=log.id,
        record_id=log.record_id,
        from_format=log.from_format,
        to_format=log.to_format,
        migrated_at=log.migrated_at.isoformat(),
    )

@router.get("/search")
def search(query: str, top_k: int = 10, db: Session = Depends(dependencies.get_db)):
    records = search_evidence_records(db, query, top_k)
    return [EvidenceRead(
        id=r.id,
        evidence_type=r.evidence_type,
        created_at=r.created_at.isoformat(),
        expires_at=r.expires_at.isoformat() if r.expires_at else None,
        metadata=r.metadata,
    ) for r in records]

@router.post("/retention/cleanup")
def cleanup(db: Session = Depends(dependencies.get_db)):
    deleted = apply_retention_cleanup(db)
    return {"deleted_records": deleted}

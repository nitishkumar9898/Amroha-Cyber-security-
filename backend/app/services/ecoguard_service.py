from sqlalchemy.orm import Session
from ..models.ecoguard import WildlifeListing, GPSForensic, EnvDataRecord, CollabRequest
from ..schemas.ecoguard import ListingCreate, GPSPayloadCreate, EnvRecordCreate, CollabRequestCreate
from ..modules.ecoguard_engine import (
    classify_listing,
    analyze_gps,
    compute_tamper_score,
    index_record,
    search_index,
    generate_agency_token,
)


# ── Wildlife Listing ─────────────────────────────────────────────────

def store_listing(db: Session, payload: ListingCreate) -> WildlifeListing:
    confidence = classify_listing(f"{payload.title} {payload.description}")
    listing = WildlifeListing(
        source_url=payload.source_url,
        title=payload.title,
        description=payload.description,
        confidence=confidence,
        additional_metadata=payload.additional_metadata,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    index_record(listing.id, f"{listing.title} {listing.description}")
    return listing

def get_listing(db: Session, listing_id: int) -> WildlifeListing:
    listing = db.query(WildlifeListing).filter(WildlifeListing.id == listing_id).first()
    if not listing:
        raise ValueError("WildlifeListing not found")
    return listing


# ── GPS Forensics ────────────────────────────────────────────────────

def store_gps_payload(db: Session, payload: GPSPayloadCreate) -> GPSForensic:
    analysis = analyze_gps(payload.raw_payload)
    record = GPSForensic(
        device_id=payload.device_id,
        raw_payload=payload.raw_payload,
        spoof_detected=analysis["spoof_detected"],
        analysis=analysis,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_gps_forensic(db: Session, forensic_id: int) -> GPSForensic:
    rec = db.query(GPSForensic).filter(GPSForensic.id == forensic_id).first()
    if not rec:
        raise ValueError("GPSForensic record not found")
    return rec


# ── Environmental Data ───────────────────────────────────────────────

def store_env_record(db: Session, payload: EnvRecordCreate) -> EnvDataRecord:
    # Extract numeric readings for tamper analysis
    readings = [v for v in payload.raw_data.values() if isinstance(v, (int, float))]
    tamper = compute_tamper_score(readings)
    record = EnvDataRecord(
        sensor_id=payload.sensor_id,
        raw_data=payload.raw_data,
        tamper_score=tamper,
        additional_metadata=payload.additional_metadata,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_env_record(db: Session, record_id: int) -> EnvDataRecord:
    rec = db.query(EnvDataRecord).filter(EnvDataRecord.id == record_id).first()
    if not rec:
        raise ValueError("EnvDataRecord not found")
    return rec


# ── Collaboration ────────────────────────────────────────────────────

def create_collab_request(db: Session, payload: CollabRequestCreate) -> CollabRequest:
    collab = CollabRequest(
        agency_name=payload.agency_name,
        case_id=payload.case_id,
        request_payload=payload.request_payload,
        status="pending",
    )
    db.add(collab)
    db.commit()
    db.refresh(collab)
    return collab

def update_collab_status(db: Session, request_id: int, status: str) -> CollabRequest:
    collab = db.query(CollabRequest).filter(CollabRequest.id == request_id).first()
    if not collab:
        raise ValueError("CollabRequest not found")
    collab.status = status
    db.commit()
    db.refresh(collab)
    return collab

def get_collab_request(db: Session, request_id: int) -> CollabRequest:
    rec = db.query(CollabRequest).filter(CollabRequest.id == request_id).first()
    if not rec:
        raise ValueError("CollabRequest not found")
    return rec


# ── Search ───────────────────────────────────────────────────────────

def search_records(db: Session, query: str, top_k: int = 10):
    ids = search_index(query, top_k)
    if not ids:
        return []
    return db.query(WildlifeListing).filter(WildlifeListing.id.in_(ids)).all()

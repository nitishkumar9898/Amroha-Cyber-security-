from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import dependencies
from ..schemas.ecoguard import (
    ListingCreate, ListingRead,
    GPSPayloadCreate, GPSPayloadRead,
    EnvRecordCreate, EnvRecordRead,
    CollabRequestCreate, CollabRequestRead,
)
from ..services.ecoguard_service import (
    store_listing, get_listing,
    store_gps_payload, get_gps_forensic,
    store_env_record, get_env_record,
    create_collab_request, update_collab_status, get_collab_request,
    search_records,
)

router = APIRouter()

# ── Wildlife Listings ─────────────────────────────────────────────────

@router.post("/listing", response_model=ListingRead)
def create_listing(payload: ListingCreate, db: Session = Depends(dependencies.get_db)):
    return store_listing(db, payload)

@router.get("/listing/{listing_id}", response_model=ListingRead)
def read_listing(listing_id: int, db: Session = Depends(dependencies.get_db)):
    return get_listing(db, listing_id)

# ── GPS Forensics ────────────────────────────────────────────────────

@router.post("/gps", response_model=GPSPayloadRead)
def upload_gps(payload: GPSPayloadCreate, db: Session = Depends(dependencies.get_db)):
    return store_gps_payload(db, payload)

@router.get("/gps/{forensic_id}", response_model=GPSPayloadRead)
def read_gps(forensic_id: int, db: Session = Depends(dependencies.get_db)):
    return get_gps_forensic(db, forensic_id)

# ── Environmental Data ───────────────────────────────────────────────

@router.post("/env", response_model=EnvRecordRead)
def upload_env(payload: EnvRecordCreate, db: Session = Depends(dependencies.get_db)):
    return store_env_record(db, payload)

@router.get("/env/{record_id}", response_model=EnvRecordRead)
def read_env(record_id: int, db: Session = Depends(dependencies.get_db)):
    return get_env_record(db, record_id)

# ── Collaboration ────────────────────────────────────────────────────

@router.post("/collab", response_model=CollabRequestRead)
def submit_collab(payload: CollabRequestCreate, db: Session = Depends(dependencies.get_db)):
    return create_collab_request(db, payload)

@router.get("/collab/{request_id}", response_model=CollabRequestRead)
def read_collab(request_id: int, db: Session = Depends(dependencies.get_db)):
    return get_collab_request(db, request_id)

@router.patch("/collab/{request_id}")
def patch_collab_status(request_id: int, status: str, db: Session = Depends(dependencies.get_db)):
    valid = {"pending", "accepted", "rejected", "closed"}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid}")
    return update_collab_status(db, request_id, status)

# ── Search ───────────────────────────────────────────────────────────

@router.get("/search")
def search(q: str, top_k: int = 10, db: Session = Depends(dependencies.get_db)):
    results = search_records(db, q, top_k)
    return [ListingRead.from_orm(r) for r in results]

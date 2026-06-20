# backend/app/routes/insider_shield.py (updated with alerts list endpoint)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..dependencies import get_db  # fallback if not present
from ..models.insider_shield import RiskScore, Alert
from ..schemas.insider_shield import (
    BehaviorIngestRequest,
    AccessEventIngestRequest,
    ExfiltrationEventIngestRequest,
    PsychProfileRequest,
    RiskScoreResponse,
    AlertResponse,
)
from ..services.insider_shield_service import (
    store_behavior_baseline,
    store_access_event,
    store_exfiltration_event,
    enrich_with_psych_profile,
    compute_and_store_risk,
    push_alert,
)

router = APIRouter(prefix="/insider", tags=["insider_shield"])

@router.post("/behavior", response_model=Dict[str, Any])
def ingest_behavior(request: BehaviorIngestRequest, db: Session = Depends(get_db)):
    baseline = store_behavior_baseline(db, request)
    compute_and_store_risk(db, request.user_id)
    return {"status": "baseline stored", "baseline_id": baseline.id}

@router.post("/access", response_model=Dict[str, Any])
def ingest_access(request: AccessEventIngestRequest, db: Session = Depends(get_db)):
    event = store_access_event(db, request)
    compute_and_store_risk(db, request.user_id)
    return {"status": "access event stored", "event_id": event.id}

@router.post("/exfiltration", response_model=Dict[str, Any])
def ingest_exfiltration(request: ExfiltrationEventIngestRequest, db: Session = Depends(get_db)):
    event = store_exfiltration_event(db, request)
    compute_and_store_risk(db, request.user_id)
    return {"status": "exfiltration event stored", "event_id": event.id}

@router.post("/psych", response_model=Dict[str, Any])
def ingest_psych_profile(request: PsychProfileRequest, db: Session = Depends(get_db)):
    profile = enrich_with_psych_profile(db, request)
    compute_and_store_risk(db, request.user_id)
    return {"status": "psych profile stored", "profile_id": profile.id}

@router.get("/risk/{user_id}", response_model=RiskScoreResponse)
def get_risk_score(user_id: int, db: Session = Depends(get_db)):
    risk = db.query(RiskScore).filter_by(user_id=user_id).order_by(RiskScore.timestamp.desc()).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk score not found")
    return risk

@router.post("/alert", response_model=AlertResponse)
def create_alert(user_id: int, severity: str, message: str, payload: Dict[str, Any] = None, db: Session = Depends(get_db)):
    alert = push_alert(db, user_id, severity, message, payload)
    return alert

@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts(limit: int = 20, db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts

# Future: WebSocket endpoint for streaming alerts can be added in backend/app/websocket/alerts.py

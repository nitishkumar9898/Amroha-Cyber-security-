from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import dependencies
from ..schemas.ipshield import (
    ExfiltrationEventCreate, ExfiltrationEventRead,
    ActorCorrelationCreate, ActorCorrelationRead,
    TradeSecretSimCreate, TradeSecretSimRead,
    IPShieldAlertRead,
)
from ..services.ipshield_service import (
    store_exfiltration_event, get_exfiltration_event, list_exfiltration_events,
    create_actor_correlation, get_actor_correlation,
    run_trade_secret_simulation, get_simulation,
    list_alerts, update_alert_status,
)
from typing import List

router = APIRouter()

# ── Exfiltration Events ──────────────────────────────────────────────

@router.post("/exfiltration", response_model=ExfiltrationEventRead)
def create_event(payload: ExfiltrationEventCreate, db: Session = Depends(dependencies.get_db)):
    """Log a potential data-exfiltration event for risk scoring."""
    return store_exfiltration_event(db, payload)

@router.get("/exfiltration/{event_id}", response_model=ExfiltrationEventRead)
def read_event(event_id: int, db: Session = Depends(dependencies.get_db)):
    return get_exfiltration_event(db, event_id)

@router.get("/exfiltrations", response_model=List[ExfiltrationEventRead])
def list_events(actor_id: str = None, db: Session = Depends(dependencies.get_db)):
    return list_exfiltration_events(db, actor_id)

# ── Actor Correlations ───────────────────────────────────────────────

@router.post("/correlation", response_model=ActorCorrelationRead)
def create_correlation(payload: ActorCorrelationCreate, db: Session = Depends(dependencies.get_db)):
    """Correlate an insider with an external actor."""
    return create_actor_correlation(db, payload)

@router.get("/correlation/{corr_id}", response_model=ActorCorrelationRead)
def read_correlation(corr_id: int, db: Session = Depends(dependencies.get_db)):
    return get_actor_correlation(db, corr_id)

# ── Trade-Secret Simulations ─────────────────────────────────────────

@router.post("/simulation", response_model=TradeSecretSimRead)
def run_simulation(payload: TradeSecretSimCreate, db: Session = Depends(dependencies.get_db)):
    """Run a trade-secret protection simulation with the given attack parameters."""
    return run_trade_secret_simulation(db, payload)

@router.get("/simulation/{sim_id}", response_model=TradeSecretSimRead)
def read_simulation(sim_id: int, db: Session = Depends(dependencies.get_db)):
    return get_simulation(db, sim_id)

# ── Alerts ───────────────────────────────────────────────────────────

@router.get("/alerts", response_model=List[IPShieldAlertRead])
def get_alerts(status: str = None, db: Session = Depends(dependencies.get_db)):
    return list_alerts(db, status)

@router.patch("/alerts/{alert_id}")
def patch_alert(alert_id: int, status: str, db: Session = Depends(dependencies.get_db)):
    valid = {"new", "investigating", "escalated", "resolved"}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid}")
    return update_alert_status(db, alert_id, status)

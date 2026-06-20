from sqlalchemy.orm import Session
from ..models.ipshield import ExfiltrationEvent, ActorCorrelation, TradeSecretSimulation, IPShieldAlert
from ..schemas.ipshield import ExfiltrationEventCreate, ActorCorrelationCreate, TradeSecretSimCreate
from ..modules.ipshield_engine import (
    compute_exfiltration_risk,
    compute_correlation_score,
    simulate_trade_secret_attack,
    detect_bulk_transfer_pattern,
)
from typing import List
import json


# ── Exfiltration Events ──────────────────────────────────────────────

def store_exfiltration_event(db: Session, payload: ExfiltrationEventCreate) -> ExfiltrationEvent:
    risk = compute_exfiltration_risk(payload.event_type, payload.data_volume_mb, payload.actor_type)
    event = ExfiltrationEvent(
        event_type=payload.event_type,
        actor_id=payload.actor_id,
        actor_type=payload.actor_type,
        risk_score=risk,
        data_volume_mb=payload.data_volume_mb,
        destination=payload.destination,
        additional_metadata=payload.additional_metadata,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Auto-generate alert if risk is high
    if risk >= 0.7:
        _create_alert(db, "exfiltration", risk, f"High-risk exfiltration via {payload.event_type} by {payload.actor_id}",
                       related_event_ids=[event.id])
    return event

def get_exfiltration_event(db: Session, event_id: int) -> ExfiltrationEvent:
    rec = db.query(ExfiltrationEvent).filter(ExfiltrationEvent.id == event_id).first()
    if not rec:
        raise ValueError("ExfiltrationEvent not found")
    return rec

def list_exfiltration_events(db: Session, actor_id: str = None) -> List[ExfiltrationEvent]:
    q = db.query(ExfiltrationEvent)
    if actor_id:
        q = q.filter(ExfiltrationEvent.actor_id == actor_id)
    return q.order_by(ExfiltrationEvent.detected_at.desc()).all()


# ── Actor Correlations ───────────────────────────────────────────────

def create_actor_correlation(db: Session, payload: ActorCorrelationCreate) -> ActorCorrelation:
    score = compute_correlation_score(payload.indicators)
    corr = ActorCorrelation(
        insider_id=payload.insider_id,
        external_id=payload.external_id,
        correlation_score=score,
        evidence_summary=payload.evidence_summary,
        indicators=payload.indicators,
        case_id=payload.case_id,
    )
    db.add(corr)
    db.commit()
    db.refresh(corr)

    # Auto-alert on strong correlation
    if score >= 0.6:
        _create_alert(db, "correlation", score,
                       f"Strong insider-external link: {payload.insider_id} ↔ {payload.external_id}",
                       related_correlation_ids=[corr.id])
    return corr

def get_actor_correlation(db: Session, corr_id: int) -> ActorCorrelation:
    rec = db.query(ActorCorrelation).filter(ActorCorrelation.id == corr_id).first()
    if not rec:
        raise ValueError("ActorCorrelation not found")
    return rec


# ── Trade-Secret Simulations ─────────────────────────────────────────

def run_trade_secret_simulation(db: Session, payload: TradeSecretSimCreate) -> TradeSecretSimulation:
    result = simulate_trade_secret_attack(payload.parameters)
    sim = TradeSecretSimulation(
        scenario_name=result["scenario_name"],
        parameters=payload.parameters,
        result=result,
        protection_score=result["protection_score"],
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)

    # Alert if simulation shows a breach
    if result.get("breach"):
        _create_alert(db, "simulation_failure", 1.0 - result["protection_score"],
                       f"Simulation '{result['scenario_name']}' resulted in breach ({result['exfiltrated_pct']}% exfiltrated)")
    return sim

def get_simulation(db: Session, sim_id: int) -> TradeSecretSimulation:
    rec = db.query(TradeSecretSimulation).filter(TradeSecretSimulation.id == sim_id).first()
    if not rec:
        raise ValueError("TradeSecretSimulation not found")
    return rec


# ── Alerts ───────────────────────────────────────────────────────────

def _create_alert(db: Session, alert_type: str, severity: float, description: str,
                  related_event_ids: list = None, related_correlation_ids: list = None):
    alert = IPShieldAlert(
        alert_type=alert_type,
        severity=severity,
        description=description,
        related_event_ids=related_event_ids,
        related_correlation_ids=related_correlation_ids,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def list_alerts(db: Session, status: str = None) -> List[IPShieldAlert]:
    q = db.query(IPShieldAlert)
    if status:
        q = q.filter(IPShieldAlert.status == status)
    return q.order_by(IPShieldAlert.created_at.desc()).all()

def update_alert_status(db: Session, alert_id: int, status: str) -> IPShieldAlert:
    alert = db.query(IPShieldAlert).filter(IPShieldAlert.id == alert_id).first()
    if not alert:
        raise ValueError("IPShieldAlert not found")
    alert.status = status
    db.commit()
    db.refresh(alert)
    return alert

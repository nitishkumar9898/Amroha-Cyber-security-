# backend/app/services/insider_shield_service.py

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from ..models.insider_shield import (
    UserBehaviorBaseline,
    AccessEvent,
    ExfiltrationEvent,
    PsychProfile,
    RiskScore,
    Alert,
)
from ..schemas.insider_shield import (
    BehaviorIngestRequest,
    AccessEventIngestRequest,
    ExfiltrationEventIngestRequest,
    PsychProfileRequest,
    RiskScoreResponse,
    AlertResponse,
)

# ---------------------------------------------------------------------------
# Ingestion helpers
# ---------------------------------------------------------------------------

def store_behavior_baseline(db: Session, req: BehaviorIngestRequest) -> UserBehaviorBaseline:
    baseline = UserBehaviorBaseline(
        user_id=req.user_id,
        feature_vector=req.feature_vector,
        timestamp=req.timestamp or datetime.utcnow(),
    )
    db.add(baseline)
    db.commit()
    db.refresh(baseline)
    return baseline


def store_access_event(db: Session, req: AccessEventIngestRequest) -> AccessEvent:
    event = AccessEvent(
        user_id=req.user_id,
        resource=req.resource,
        action=req.action,
        outcome=req.outcome,
        timestamp=req.timestamp or datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def store_exfiltration_event(db: Session, req: ExfiltrationEventIngestRequest) -> ExfiltrationEvent:
    event = ExfiltrationEvent(
        user_id=req.user_id,
        data_size_bytes=req.data_size_bytes,
        entropy=req.entropy,
        details=req.details,
        timestamp=req.timestamp or datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

# ---------------------------------------------------------------------------
# Psychology integration (uses existing module)
# ---------------------------------------------------------------------------

def enrich_with_psych_profile(db: Session, req: PsychProfileRequest) -> PsychProfile:
    # Simple upsert logic
    profile = db.query(PsychProfile).filter_by(user_id=req.user_id).first()
    if profile:
        profile.profile_json = req.profile_json
        profile.timestamp = req.timestamp or datetime.utcnow()
    else:
        profile = PsychProfile(
            user_id=req.user_id,
            profile_json=req.profile_json,
            timestamp=req.timestamp or datetime.utcnow(),
        )
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

# ---------------------------------------------------------------------------
# Risk scoring (placeholder – replace with proper ML model later)
# ---------------------------------------------------------------------------

def calculate_risk_score(
    behavior_score: float,
    exfil_score: float,
    psych_factor: float,
) -> float:
    # Weighted sum – tunable weights
    return 0.5 * behavior_score + 0.3 * exfil_score + 0.2 * psych_factor


def compute_and_store_risk(db: Session, user_id: int) -> RiskScore:
    # Placeholder: fetch latest events and compute simple heuristics
    behavior = (
        db.query(UserBehaviorBaseline)
        .filter_by(user_id=user_id)
        .order_by(UserBehaviorBaseline.timestamp.desc())
        .first()
    )
    exfil = (
        db.query(ExfiltrationEvent)
        .filter_by(user_id=user_id)
        .order_by(ExfiltrationEvent.timestamp.desc())
        .first()
    )
    psych = (
        db.query(PsychProfile).filter_by(user_id=user_id).first()
    )

    # Very naive scores
    behavior_score = 0.0 if not behavior else 0.2
    exfil_score = 0.0 if not exfil else 0.5
    psych_factor = 0.0 if not psych else 0.3

    overall = calculate_risk_score(behavior_score, exfil_score, psych_factor)
    risk = RiskScore(
        user_id=user_id,
        score=overall,
        reason="Simple heuristic",
        timestamp=datetime.utcnow(),
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk

# ---------------------------------------------------------------------------
# Alert handling
# ---------------------------------------------------------------------------

def push_alert(
    db: Session,
    user_id: int,
    severity: str,
    message: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Alert:
    alert = Alert(
        user_id=user_id,
        severity=severity,
        message=message,
        payload=payload,
        created_at=datetime.utcnow(),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    # In a real system you would also emit via WebSocket here
    return alert

# ---------------------------------------------------------------------------
# Differential privacy placeholder (adds Laplace noise to aggregates)
# ---------------------------------------------------------------------------

def apply_differential_privacy(value: float, epsilon: float = 1.0) -> float:
    import numpy as np
    scale = 1.0 / epsilon
    noise = np.random.laplace(0, scale)
    return float(value + noise)

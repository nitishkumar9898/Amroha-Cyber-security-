# backend/app/auto_defend/api.py
"""AutoDefend API routes.
Provides endpoints to manually trigger anomalies, retrieve recovery logs, and get patch suggestions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from ..services.auto_defend_service import AutoDefendService
from ..tasks.anomaly_watcher import enqueue_event

router = APIRouter(prefix="/api/auto_defend", tags=["AutoDefend"])

@router.post("/trigger", response_model=dict)
def trigger_anomaly(event: dict):
    """Manually submit an anomaly event.
    The event is enqueued and will be processed by the background watcher.
    """
    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="Invalid event payload")
    enqueue_event(event)
    return {"status": "enqueued", "event": event}

@router.get("/logs", response_model=list)
def get_recovery_logs(limit: int = 100):
    """Return recent audit‑proof recovery logs."""
    logs = AutoDefendService.get_logs(limit)
    # Serialize to dicts (SQLAlchemy objects)
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "event_type": log.event_type,
            "detail": log.detail,
            "zkp_signature": log.zkp_signature,
        }
        for log in logs
    ]

@router.get("/patches/{vuln_id}", response_model=list)
def get_patch_suggestions(vuln_id: str):
    """Return suggested patches for a vulnerability ID (e.g., CVE)."""
    return AutoDefendService.suggest_patches(vuln_id)

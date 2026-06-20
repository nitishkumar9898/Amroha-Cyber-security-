from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.responseforge import Incident, ActionLog
from app.schemas.responseforge import IncidentCreate, IncidentOut, PlaybookRequest
from app.modules.responseforge.playbook_engine import playbook_engine
from app.modules.responseforge.containment_advisor import containment_advisor
from app.modules.responseforge.forensics_analyzer import forensics_analyzer
from app.modules.responseforge.self_healing_bridge import self_healing_bridge
from app.modules.responseforge.incident_reporter import incident_reporter

router = APIRouter()

@router.post("/incidents", response_model=IncidentOut)
async def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    db_incident = Incident(
        incident_type=incident.incident_type,
        telemetry_data=incident.telemetry_data
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

@router.get("/incidents/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.post("/playbooks/generate")
async def generate_playbook(request: PlaybookRequest):
    playbook = await playbook_engine.generate_playbook(request.incident_type, request.context)
    return {"playbook": playbook}

@router.post("/containment/suggest")
async def suggest_containment(telemetry: Dict[str, Any]):
    suggestions = await containment_advisor.suggest_containment_actions(telemetry)
    return {"suggestions": suggestions}

@router.post("/forensics/analyze/{incident_id}")
async def analyze_forensics(incident_id: int, artifacts: Dict[str, Any], db: Session = Depends(get_db)):
    analysis = await forensics_analyzer.analyze_artifacts(str(incident_id), artifacts)
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        incident.root_cause = analysis.get("root_cause")
        db.commit()
        
    return analysis

@router.post("/actions/execute")
async def execute_actions(actions: List[Dict[str, Any]]):
    result = await self_healing_bridge.execute_actions(actions)
    return result

@router.get("/reports/generate/{incident_id}")
async def generate_report(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    incident_data = {
        "incident_id": str(incident.id),
        "root_cause": incident.root_cause,
        "timeline": [f"Incident created at {incident.created_at}"],
        "actions_taken": [{"action": act.action_type, "target": act.target} for act in incident.actions]
    }
    
    report = await incident_reporter.generate_report(incident_data)
    return {"report": report}

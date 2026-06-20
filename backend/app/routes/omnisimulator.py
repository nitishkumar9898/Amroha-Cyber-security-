from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.omnisimulator import (
    ScenarioCreateRequest, ScenarioResult,
    EventTriggerRequest, EventTriggerResult,
    GlobalStateResponse
)
from ..services.omnisimulator_service import OmniSimulatorService

router = APIRouter()

@router.post("/launch-scenario", response_model=ScenarioResult)
def launch_scenario(payload: ScenarioCreateRequest, db: Session = Depends(get_db)):
    try:
        return OmniSimulatorService.launch_scenario(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger-event", response_model=EventTriggerResult)
def trigger_event(payload: EventTriggerRequest, db: Session = Depends(get_db)):
    try:
        return OmniSimulatorService.trigger_event(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/global-state/{scenario_id}", response_model=GlobalStateResponse)
def get_global_state(scenario_id: str, db: Session = Depends(get_db)):
    try:
        return OmniSimulatorService.get_global_state(db, scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

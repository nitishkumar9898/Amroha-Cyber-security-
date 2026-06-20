from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.autoguard import VehicleLog, MalwareAlert, SwarmAttackScenario
from app.schemas.autoguard import VehicleLogCreate, VehicleLogRead, MalwareAlertRead, SwarmScenarioCreate, SwarmScenarioRead
from app.services.autoguard_service import store_vehicle_log, run_malware_detection, run_swarm_simulation

router = APIRouter()

@router.post("/log", response_model=VehicleLogRead)
def upload_log(payload: VehicleLogCreate, db: Session = Depends(get_db)):
    try:
        return store_vehicle_log(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/{vehicle_id}", response_model=List[MalwareAlertRead])
def get_alerts(vehicle_id: str, db: Session = Depends(get_db)):
    alerts = db.query(MalwareAlert).filter(MalwareAlert.vehicle_id == vehicle_id).all()
    return alerts

@router.post("/simulate", response_model=SwarmScenarioRead)
def simulate_swarm(params: SwarmScenarioCreate, db: Session = Depends(get_db)):
    try:
        return run_swarm_simulation(db, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.resilientforge import SimulationRequest, SimulationReport, BackupVerifyRequest, BackupVerifyResult, HealRequest, HealResult
from ..services.resilientforge_service import ResilientForgeService

router = APIRouter()

@router.post("/simulate-disaster", response_model=SimulationReport)
def simulate_disaster(payload: SimulationRequest, db: Session = Depends(get_db)):
    try:
        return ResilientForgeService.simulate_disaster(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-backup", response_model=BackupVerifyResult)
def verify_backup(payload: BackupVerifyRequest, db: Session = Depends(get_db)):
    try:
        return ResilientForgeService.verify_backup(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger-heal", response_model=HealResult)
def trigger_heal(payload: HealRequest, db: Session = Depends(get_db)):
    try:
        return ResilientForgeService.trigger_heal(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

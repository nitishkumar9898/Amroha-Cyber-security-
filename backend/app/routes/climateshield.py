from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.climateshield import InfraAttackRequest, InfraAttackResult, ClimateSimRequest, ClimateSimResult, ResiliencePlanRequest, ResiliencePlanResult
from ..services.climateshield_service import ClimateShieldService

router = APIRouter()

@router.post("/simulate-infra-attack", response_model=InfraAttackResult)
def simulate_infra_attack(payload: InfraAttackRequest, db: Session = Depends(get_db)):
    try:
        return ClimateShieldService.simulate_infra_attack(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-climate-manipulation", response_model=ClimateSimResult)
def simulate_climate_manipulation(payload: ClimateSimRequest, db: Session = Depends(get_db)):
    try:
        return ClimateShieldService.simulate_climate_manipulation(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-resilience-plan", response_model=ResiliencePlanResult)
def generate_resilience_plan(payload: ResiliencePlanRequest, db: Session = Depends(get_db)):
    try:
        return ClimateShieldService.generate_resilience_plan(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

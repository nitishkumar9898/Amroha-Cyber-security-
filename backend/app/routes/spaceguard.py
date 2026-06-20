from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.spaceguard import SatCommRequest, SatCommResult, OrbitalSimRequest, OrbitalSimResult, AssetProtectionRequest, AssetProtectionResult
from ..services.spaceguard_service import SpaceGuardService

router = APIRouter()

@router.post("/analyze-sat-comm", response_model=SatCommResult)
def analyze_sat_comm(payload: SatCommRequest, db: Session = Depends(get_db)):
    try:
        return SpaceGuardService.analyze_sat_comm(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-orbital-attack", response_model=OrbitalSimResult)
def simulate_orbital_attack(payload: OrbitalSimRequest, db: Session = Depends(get_db)):
    try:
        return SpaceGuardService.simulate_orbital_attack(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/protect-asset", response_model=AssetProtectionResult)
def protect_asset(payload: AssetProtectionRequest, db: Session = Depends(get_db)):
    try:
        return SpaceGuardService.protect_asset(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

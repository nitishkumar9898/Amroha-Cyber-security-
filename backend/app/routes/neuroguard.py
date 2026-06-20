from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.neuroguard import NeuralTelemetryRequest, NeuralScanResult, BCISimRequest, BCISimResult, PrivacyEnforcementRequest, PrivacyEnforcementResult
from ..services.neuroguard_service import NeuroGuardService

router = APIRouter()

@router.post("/analyze-telemetry", response_model=NeuralScanResult)
def analyze_telemetry(payload: NeuralTelemetryRequest, db: Session = Depends(get_db)):
    try:
        return NeuroGuardService.analyze_telemetry(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-bci-hack", response_model=BCISimResult)
def simulate_bci_hack(payload: BCISimRequest, db: Session = Depends(get_db)):
    try:
        return NeuroGuardService.simulate_bci_hack(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enforce-privacy", response_model=PrivacyEnforcementResult)
def enforce_privacy(payload: PrivacyEnforcementRequest, db: Session = Depends(get_db)):
    try:
        return NeuroGuardService.enforce_privacy(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

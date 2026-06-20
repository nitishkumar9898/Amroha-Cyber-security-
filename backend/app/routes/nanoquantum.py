from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.nanoquantum import NanoScanRequest, NanoScanResult, NanoSimRequest, NanoSimResult, HardwareValidationRequest, HardwareValidationResult
from ..services.nanoquantum_service import NanoQuantumService

router = APIRouter()

@router.post("/analyze-sensor", response_model=NanoScanResult)
def analyze_sensor(payload: NanoScanRequest, db: Session = Depends(get_db)):
    try:
        return NanoQuantumService.analyze_sensor(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-nano-threat", response_model=NanoSimResult)
def simulate_nano_threat(payload: NanoSimRequest, db: Session = Depends(get_db)):
    try:
        return NanoQuantumService.simulate_nano_threat(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-hardware", response_model=HardwareValidationResult)
def validate_hardware(payload: HardwareValidationRequest, db: Session = Depends(get_db)):
    try:
        return NanoQuantumService.validate_hardware(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

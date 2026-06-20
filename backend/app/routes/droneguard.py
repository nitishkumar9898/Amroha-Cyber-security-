from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.droneguard import TelemetryRequest, TelemetryResult, MalwareAnalysisRequest, MalwareAnalysisResult, SwarmSimulationRequest, SwarmSimulationResult, EvidenceComplianceRequest, EvidenceComplianceResult
from ..services.droneguard_service import DroneGuardService

router = APIRouter()

@router.post("/analyze-telemetry", response_model=TelemetryResult)
def analyze_telemetry(payload: TelemetryRequest, db: Session = Depends(get_db)):
    try:
        return DroneGuardService.analyze_telemetry(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-malware", response_model=MalwareAnalysisResult)
def analyze_malware(payload: MalwareAnalysisRequest, db: Session = Depends(get_db)):
    try:
        return DroneGuardService.analyze_malware(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-swarm", response_model=SwarmSimulationResult)
def simulate_swarm(payload: SwarmSimulationRequest, db: Session = Depends(get_db)):
    try:
        return DroneGuardService.simulate_swarm(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/secure-evidence", response_model=EvidenceComplianceResult)
def secure_evidence(payload: EvidenceComplianceRequest, db: Session = Depends(get_db)):
    try:
        return DroneGuardService.secure_evidence(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

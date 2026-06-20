from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.gridshield import ScadaAnalysisRequest, ScadaAnalysisResult, PhysicalSimulationRequest, PhysicalSimulationResult, ResiliencePlanRequest, ResiliencePlanResult, ThreatForecastRequest, ThreatForecastResult
from ..services.gridshield_service import GridShieldService

router = APIRouter()

@router.post("/analyze-scada", response_model=ScadaAnalysisResult)
def analyze_scada(payload: ScadaAnalysisRequest, db: Session = Depends(get_db)):
    try:
        return GridShieldService.analyze_scada(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-physical", response_model=PhysicalSimulationResult)
def simulate_physical(payload: PhysicalSimulationRequest, db: Session = Depends(get_db)):
    try:
        return GridShieldService.simulate_physical(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plan-resilience", response_model=ResiliencePlanResult)
def plan_resilience(payload: ResiliencePlanRequest, db: Session = Depends(get_db)):
    try:
        return GridShieldService.plan_resilience(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forecast-threat", response_model=ThreatForecastResult)
def forecast_threat(payload: ThreatForecastRequest, db: Session = Depends(get_db)):
    try:
        return GridShieldService.forecast_threat(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

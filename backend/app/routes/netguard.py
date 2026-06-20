from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.netguard import NodeRegister, NodeResponse, TrafficIngestRequest, AnalysisResult, SimulationRequest, SimulationReport
from ..services.netguard_service import NetGuardService

router = APIRouter()

@router.post("/nodes", response_model=NodeResponse)
def register_node(payload: NodeRegister, db: Session = Depends(get_db)):
    try:
        return NetGuardService.register_node(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-traffic", response_model=AnalysisResult)
def analyze_traffic(payload: TrafficIngestRequest, db: Session = Depends(get_db)):
    try:
        return NetGuardService.analyze_traffic(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-attack", response_model=SimulationReport)
def simulate_attack(payload: SimulationRequest, db: Session = Depends(get_db)):
    try:
        return NetGuardService.simulate_attack(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

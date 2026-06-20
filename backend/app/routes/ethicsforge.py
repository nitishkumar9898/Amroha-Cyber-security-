from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.ethicsforge import PolicyCreate, PolicyOut, ActionEvaluationRequest, ActionEvaluationResult, BiasScanRequest, BiasScanResult, TransparencyReportOut
from ..services.ethicsforge_service import EthicsForgeService

router = APIRouter()

@router.post("/policies", response_model=PolicyOut)
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)):
    try:
        return EthicsForgeService.create_policy(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan-bias", response_model=BiasScanResult)
def scan_bias(payload: BiasScanRequest, db: Session = Depends(get_db)):
    try:
        return EthicsForgeService.scan_bias(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate-action", response_model=ActionEvaluationResult)
def evaluate_action(payload: ActionEvaluationRequest, db: Session = Depends(get_db)):
    try:
        return EthicsForgeService.evaluate_action(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transparency-report/{log_id}", response_model=TransparencyReportOut)
def generate_transparency_report(log_id: int, db: Session = Depends(get_db)):
    try:
        return EthicsForgeService.generate_transparency_report(db, log_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

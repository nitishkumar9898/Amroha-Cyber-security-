from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.zerotrustforge import (
    AuthCheckRequest, AuthCheckResult, 
    SegmentCreateRequest, SegmentCreateResult,
    AccessEvaluationRequest, AccessEvaluationResult,
    PolicyEnforcementRequest, PolicyEnforcementResult
)
from ..services.zerotrustforge_service import ZeroTrustForgeService

router = APIRouter()

@router.post("/authenticate", response_model=AuthCheckResult)
def authenticate(payload: AuthCheckRequest, db: Session = Depends(get_db)):
    try:
        return ZeroTrustForgeService.authenticate(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-segment", response_model=SegmentCreateResult)
def create_segment(payload: SegmentCreateRequest, db: Session = Depends(get_db)):
    try:
        return ZeroTrustForgeService.create_segment(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate-access", response_model=AccessEvaluationResult)
def evaluate_access(payload: AccessEvaluationRequest, db: Session = Depends(get_db)):
    try:
        return ZeroTrustForgeService.evaluate_access(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enforce-policy", response_model=PolicyEnforcementResult)
def enforce_policy(payload: PolicyEnforcementRequest, db: Session = Depends(get_db)):
    try:
        return ZeroTrustForgeService.enforce_policy(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

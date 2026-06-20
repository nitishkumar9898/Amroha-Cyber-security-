from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.risknova import AssessRequest, FullAssessmentResponse
from ..services import risknova_service

router = APIRouter()

@router.post("/assess", response_model=FullAssessmentResponse)
def assess_technology(request: AssessRequest, db: Session = Depends(get_db)):
    """
    Conducts a proactive risk assessment on an emerging technology, 
    forecasts scenarios, and generates a mitigation roadmap.
    """
    try:
        return risknova_service.assess_emerging_tech(db, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

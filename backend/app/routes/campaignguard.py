from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.campaignguard import CampaignAnalyzeRequest, CampaignAnalysisResponse
from ..services import campaignguard_service

router = APIRouter()

@router.post("/analyze", response_model=CampaignAnalysisResponse)
def analyze_campaign(request: CampaignAnalyzeRequest, db: Session = Depends(get_db)):
    """
    Analyzes a deepfake or influence payload to track propagation,
    detect bot amplification swarms, and generate takedown reports.
    """
    try:
        return campaignguard_service.analyze_campaign(db, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

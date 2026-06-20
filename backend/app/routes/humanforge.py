from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.humanforge import PhishingDetectionRequest, PhishingDetectionResult, ManipulationAnalysisRequest, ManipulationAnalysisResult, AwarenessSimulationRequest, AwarenessSimulationResult, InsiderLinkRequest, InsiderLinkResult
from ..services.humanforge_service import HumanForgeService

router = APIRouter()

@router.post("/detect-phishing", response_model=PhishingDetectionResult)
def detect_phishing(payload: PhishingDetectionRequest, db: Session = Depends(get_db)):
    try:
        return HumanForgeService.detect_phishing(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-manipulation", response_model=ManipulationAnalysisResult)
def analyze_manipulation(payload: ManipulationAnalysisRequest, db: Session = Depends(get_db)):
    try:
        return HumanForgeService.analyze_manipulation(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-awareness", response_model=AwarenessSimulationResult)
def simulate_awareness(payload: AwarenessSimulationRequest, db: Session = Depends(get_db)):
    try:
        return HumanForgeService.simulate_awareness(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/link-insider", response_model=InsiderLinkResult)
def link_insider(payload: InsiderLinkRequest, db: Session = Depends(get_db)):
    try:
        return HumanForgeService.link_insider(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

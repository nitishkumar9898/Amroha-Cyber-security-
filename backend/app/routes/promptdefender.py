from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.promptdefender import PromptInjectionRequest, PromptInjectionResult, HallucinationRequest, HallucinationResult, SyntheticForensicsRequest, SyntheticForensicsResult, CrossModuleLinkRequest, CrossModuleLinkResult
from ..services.promptdefender_service import PromptDefenderService

router = APIRouter()

@router.post("/detect-injection", response_model=PromptInjectionResult)
def detect_injection(payload: PromptInjectionRequest, db: Session = Depends(get_db)):
    try:
        return PromptDefenderService.detect_injection(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-hallucination", response_model=HallucinationResult)
def analyze_hallucination(payload: HallucinationRequest, db: Session = Depends(get_db)):
    try:
        return PromptDefenderService.analyze_hallucination(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-synthetic", response_model=SyntheticForensicsResult)
def analyze_synthetic(payload: SyntheticForensicsRequest, db: Session = Depends(get_db)):
    try:
        return PromptDefenderService.analyze_synthetic(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/link-osint", response_model=CrossModuleLinkResult)
def link_osint(payload: CrossModuleLinkRequest, db: Session = Depends(get_db)):
    try:
        return PromptDefenderService.link_module(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

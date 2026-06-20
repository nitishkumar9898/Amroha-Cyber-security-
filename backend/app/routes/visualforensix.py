from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.visualforensix import (
    MediaIngestRequest, MediaIngestResult,
    VisualAnalysisRequest, VisualAnalysisResult,
    ReportGenerationRequest, ReportGenerationResult
)
from ..services.visualforensix_service import VisualForensixService

router = APIRouter()

@router.post("/ingest", response_model=MediaIngestResult)
def ingest_media(payload: MediaIngestRequest, db: Session = Depends(get_db)):
    try:
        return VisualForensixService.ingest_media(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=VisualAnalysisResult)
def analyze_media(payload: VisualAnalysisRequest, db: Session = Depends(get_db)):
    try:
        return VisualForensixService.analyze_media(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-report", response_model=ReportGenerationResult)
def generate_report(payload: ReportGenerationRequest, db: Session = Depends(get_db)):
    try:
        return VisualForensixService.generate_report(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

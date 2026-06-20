from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.metaforge import MetricIngestRequest, MetricIngestResult, EvolutionRequest, EvolutionResult, InternalAnomalyRequest, InternalAnomalyResult
from ..services.metaforge_service import MetaForgeService

router = APIRouter()

@router.post("/ingest-metric", response_model=MetricIngestResult)
def ingest_metric(payload: MetricIngestRequest, db: Session = Depends(get_db)):
    try:
        return MetaForgeService.ingest_metric(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/manage-evolution", response_model=EvolutionResult)
def manage_evolution(payload: EvolutionRequest, db: Session = Depends(get_db)):
    try:
        return MetaForgeService.manage_evolution(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-anomaly", response_model=InternalAnomalyResult)
def detect_anomaly(payload: InternalAnomalyRequest, db: Session = Depends(get_db)):
    try:
        return MetaForgeService.detect_anomaly(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

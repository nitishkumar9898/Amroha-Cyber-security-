from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import correlix_models as models
from ..schemas import correlix_schemas as schemas
from ..modules import correlix_engine as engine

router = APIRouter(prefix="/correlix", tags=["Correlix"])

@router.post("/correlate", response_model=schemas.CorrelationJobRead)
def correlate_evidence(job: schemas.CorrelationJobCreate, db: Session = Depends(get_db)):
    result = engine.run_correlation(job.source_module, job.target_module)
    
    db_job = models.CorrelationJob(
        source_module=job.source_module,
        target_module=job.target_module,
        confidence_score=result["confidence_score"],
        status=result["status"]
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.get("/jobs", response_model=List[schemas.CorrelationJobRead])
def get_jobs(db: Session = Depends(get_db)):
    return db.query(models.CorrelationJob).all()

@router.get("/jobs/{job_id}/graph", response_model=schemas.CorrelationGraphResponse)
def get_correlation_graph(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.CorrelationJob).filter(models.CorrelationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    result = engine.run_correlation(job.source_module, job.target_module)
    
    return schemas.CorrelationGraphResponse(
        job_id=job.id,
        nodes=result["nodes"],
        links=result["links"]
    )

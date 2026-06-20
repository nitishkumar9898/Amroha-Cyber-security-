"""
OSINTForge FastAPI Routes
Defines HTTP endpoints for starting crawling jobs, querying jobs,
fetching the actor network, checking misinformation events, and getting AI summaries.
"""
from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.osint import CrawlJob, MisinformationEvent
from ..schemas.osint import (
    CrawlJobCreate,
    CrawlJobOut,
    MisinformationEventOut,
    ActorProfileOut
)
from ..services.osint_service import OSINTForgeService

router = APIRouter()

@router.post("/osint/crawl", response_model=CrawlJobOut)
def start_crawl(job: CrawlJobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    new_job = CrawlJob(
        platform=job.platform,
        query=job.query,
        schedule=job.schedule or "once",
        status="running"
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Queue background task
    background_tasks.add_task(OSINTForgeService.crawl_and_process, new_job.id, db)
    return new_job

@router.get("/osint/job/{job_id}", response_model=CrawlJobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/osint/network")
def get_network(platform: str = None, db: Session = Depends(get_db)):
    return OSINTForgeService.get_actor_network(db, platform)

@router.get("/osint/misinformation", response_model=List[MisinformationEventOut])
def get_misinformation(db: Session = Depends(get_db)):
    events = db.query(MisinformationEvent).all()
    return events

@router.get("/osint/summary/{query}")
def get_summary(query: str, db: Session = Depends(get_db)):
    summary_text = OSINTForgeService.generate_ai_summary(db, query)
    return {"summary": summary_text}

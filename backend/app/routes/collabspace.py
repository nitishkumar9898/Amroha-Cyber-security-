from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import collabspace_models as models
from ..schemas import collabspace_schemas as schemas
from ..modules import collabspace_engine as engine

router = APIRouter(prefix="/collabspace", tags=["CollabSpace"])

@router.post("/workspaces", response_model=schemas.WorkspaceRead)
def create_workspace(ws: schemas.WorkspaceCreate, db: Session = Depends(get_db)):
    db_ws = models.InvestigationWorkspace(**ws.dict())
    db.add(db_ws)
    db.commit()
    db.refresh(db_ws)
    return db_ws

@router.get("/workspaces", response_model=List[schemas.WorkspaceRead])
def get_workspaces(db: Session = Depends(get_db)):
    return db.query(models.InvestigationWorkspace).all()

@router.post("/annotations", response_model=schemas.AnnotationRead)
def add_annotation(ann: schemas.AnnotationCreate, db: Session = Depends(get_db)):
    db_ann = models.WorkspaceAnnotation(**ann.dict())
    db.add(db_ann)
    db.commit()
    db.refresh(db_ann)
    # Simulate real-time sync via engine
    engine.sync_workspace_state(ann.workspace_id, ann.author, "Added Annotation")
    return db_ann

@router.get("/workspaces/{ws_id}/annotations", response_model=List[schemas.AnnotationRead])
def get_annotations(ws_id: int, db: Session = Depends(get_db)):
    return db.query(models.WorkspaceAnnotation).filter(models.WorkspaceAnnotation.workspace_id == ws_id).all()

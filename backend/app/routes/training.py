from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, services, models
from ..database import get_db
from ..auth import get_current_user, User

router = APIRouter()

@router.post("/start", response_model=schemas.TrainingSessionResponse)
def start_training(payload: schemas.TrainingSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Ensure the user_id matches current user for security
    if payload.user_id != current_user.username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User ID mismatch")
    session = services.training_service.TrainingService.start_session(db, payload)
    return session

@router.post("/submit", response_model=schemas.TrainingResultResponse)
def submit_result(payload: schemas.TrainingResultCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify session belongs to user
    sess = db.query(models.training.TrainingSession).filter(models.training.TrainingSession.id == payload.session_id).first()
    if not sess or sess.user_id != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training session not found or unauthorized")
    result = services.training_service.TrainingService.submit_result(db, payload)
    return result

@router.get("/results/{session_id}", response_model=list[schemas.TrainingResultResponse])
def get_results(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sess = db.query(models.training.TrainingSession).filter(models.training.TrainingSession.id == session_id).first()
    if not sess or sess.user_id != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training session not found or unauthorized")
    results = services.training_service.TrainingService.get_results(db, session_id)
    return results

@router.get("/score/{session_id}", response_model=float)
def get_score(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify session belongs to user
    sess = db.query(models.training.TrainingSession).filter(models.training.TrainingSession.id == session_id).first()
    if not sess or sess.user_id != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training session not found or unauthorized")
    return services.training_service.TrainingService.calculate_score(db, session_id)

@router.get("/hints/{session_id}", response_model=list)
def get_hints(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sess = db.query(models.training.TrainingSession).filter(models.training.TrainingSession.id == session_id).first()
    if not sess or sess.user_id != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training session not found or unauthorized")
    return services.training_service.TrainingService.get_hints(db, session_id)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import dependencies
from ..schemas.electguard import VoteLogCreate, VoteLogRead, MisinformationAlertRead, VoterDataAnomalyRead
from ..services.electguard_service import store_vote_log, run_integrity_check, detect_misinformation_alert, analyze_voter_anomaly

router = APIRouter()

@router.post("/vote_log", response_model=VoteLogRead)
def upload_vote_log(payload: VoteLogCreate, db: Session = Depends(dependencies.get_db)):
    return store_vote_log(db, payload)

@router.get("/integrity/{election_id}")
def get_integrity(election_id: str, db: Session = Depends(dependencies.get_db)):
    return run_integrity_check(db, election_id)

@router.post("/misinformation", response_model=MisinformationAlertRead)
def submit_misinformation(source_payload: dict, db: Session = Depends(dependencies.get_db)):
    # source_payload should contain at least a "source" and "text" field
    if "source" not in source_payload or "text" not in source_payload:
        raise HTTPException(status_code=400, detail="source and text fields required")
    return detect_misinformation_alert(db, source_payload)

@router.get("/anomalies/{voter_id_hashed}", response_model=VoterDataAnomalyRead)
def get_voter_anomaly(voter_id_hashed: str, election_id: str, db: Session = Depends(dependencies.get_db)):
    return analyze_voter_anomaly(db, voter_id_hashed, election_id)

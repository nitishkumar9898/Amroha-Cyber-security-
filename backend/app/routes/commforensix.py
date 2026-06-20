from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.commforensix import MessageUpload, CallUpload, TrafficPatternResponse, SideChannelResult, EvidenceExport
from ..modules import commforensix_engine

router = APIRouter()

@router.post('/messages', response_model=MessageUpload)
def upload_messages(request: MessageUpload, db: Session = Depends(get_db)):
    try:
        scan_id = commforensix_engine.run_pqc_scan(db, request)
        return {"scan_id": scan_id, "messages": request.messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/calls', response_model=CallUpload)
def upload_calls(request: CallUpload, db: Session = Depends(get_db)):
    # Placeholder: store calls similarly
    return request

@router.get('/traffic/{scan_id}', response_model=TrafficPatternResponse)
def get_traffic(scan_id: str, db: Session = Depends(get_db)):
    return commforensix_engine.analyze_traffic(db, scan_id)

@router.get('/timing/{call_id}', response_model=SideChannelResult)
def get_timing(call_id: str, db: Session = Depends(get_db)):
    return commforensix_engine.simulate_timing_attack(db, call_id)

@router.get('/evidence/{case_id}', response_model=EvidenceExport)
def get_evidence(case_id: str, db: Session = Depends(get_db)):
    return commforensix_engine.extract_evidence(db, case_id)

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.quantumsafe import PQCScanRequest, PQCScanResponse
from ..services import quantumsafe_service

router = APIRouter()

@router.post('/scan', response_model=PQCScanResponse)
def scan(request: PQCScanRequest, db: Session = Depends(get_db)):
    """Run a PQC scan on the provided assets."""
    try:
        return quantumsafe_service.run_pqc_scan(db, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/results/{scan_id}', response_model=PQCScanResponse)
def results(scan_id: str, db: Session = Depends(get_db)):
    """Retrieve scan results for a given scan_id."""
    try:
        return quantumsafe_service.get_pqc_results(db, scan_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

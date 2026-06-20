from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.globaljurix import JurisdictionRequest, JurisdictionResult, EvidenceSharingRequest, EvidenceSharingResult, MLATRequest, MLATResult, AgencyLinkRequest, AgencyLinkResult
from ..services.globaljurix_service import GlobalJurixService

router = APIRouter()

@router.post("/map-jurisdiction", response_model=JurisdictionResult)
def map_jurisdiction(payload: JurisdictionRequest, db: Session = Depends(get_db)):
    try:
        return GlobalJurixService.map_jurisdiction(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/package-evidence", response_model=EvidenceSharingResult)
def package_evidence(payload: EvidenceSharingRequest, db: Session = Depends(get_db)):
    try:
        return GlobalJurixService.package_evidence(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-mlat", response_model=MLATResult)
def check_mlat(payload: MLATRequest, db: Session = Depends(get_db)):
    try:
        return GlobalJurixService.check_mlat(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/link-collabguard", response_model=AgencyLinkResult)
def link_collabguard(payload: AgencyLinkRequest, db: Session = Depends(get_db)):
    try:
        return GlobalJurixService.link_collabguard(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

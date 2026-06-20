from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.apthunter import (
    AnalyzePersistenceRequest,
    CampaignReconstructionRequest,
    PersistenceArtifactRead,
    APTCampaignRead,
    ThreatActorRead
)
from ..services import apthunter_service

router = APIRouter()

@router.post("/analyze-persistence", response_model=List[PersistenceArtifactRead])
def analyze_persistence_endpoint(request: AnalyzePersistenceRequest, db: Session = Depends(get_db)):
    """
    Analyzes raw system scan data to detect stealthy persistence artifacts.
    """
    try:
        results = apthunter_service.analyze_persistence(db, request)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/map-campaign", response_model=APTCampaignRead)
def map_campaign_endpoint(request: CampaignReconstructionRequest, db: Session = Depends(get_db)):
    """
    Reconstructs an APT campaign and attributes a threat actor based on mapped TTPs from GNN simulation.
    """
    try:
        campaign = apthunter_service.map_and_reconstruct_campaign(db, request)
        return campaign
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/actors", response_model=List[ThreatActorRead])
def get_threat_actors_endpoint(db: Session = Depends(get_db)):
    """
    Retrieves the list of known threat actors in the database.
    """
    return apthunter_service.get_threat_actors(db)

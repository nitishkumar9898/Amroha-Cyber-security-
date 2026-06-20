from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..models.apthunter import ThreatActor, APTCampaign, TTPMapping, PersistenceArtifact
from ..schemas.apthunter import (
    AnalyzePersistenceRequest,
    CampaignReconstructionRequest,
    PersistenceArtifactRead,
    TTPMappingRead,
    APTCampaignRead
)
from ..modules.apthunter_engine import detect_stealthy_persistence, map_ttps_gnn, reconstruct_campaign

def analyze_persistence(db: Session, request: AnalyzePersistenceRequest) -> List[PersistenceArtifact]:
    raw_scan = request.scan_data
    detected = detect_stealthy_persistence(raw_scan)
    
    saved_artifacts = []
    for art in detected:
        record = PersistenceArtifact(
            artifact_type=art["artifact_type"],
            artifact_value=art["artifact_value"],
            stealth_score=art["stealth_score"]
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        saved_artifacts.append(record)
        
    return saved_artifacts

def map_and_reconstruct_campaign(db: Session, request: CampaignReconstructionRequest) -> APTCampaign:
    # Retrieve the artifacts
    artifacts = db.query(PersistenceArtifact).filter(PersistenceArtifact.id.in_(request.artifact_ids)).all()
    if not artifacts:
        raise ValueError("No valid artifacts provided for reconstruction.")
        
    art_dicts = [{"artifact_type": a.artifact_type, "artifact_value": a.artifact_value, "stealth_score": a.stealth_score, "id": a.id} for a in artifacts]
    
    # 1. Map TTPs using GNN simulation
    ttp_maps = map_ttps_gnn(art_dicts)
    
    # 2. Reconstruct Campaign
    camp_name, actor_id, confidence = reconstruct_campaign(ttp_maps)
    
    # Ensure Threat Actor exists if id provided (mocking a DB seed)
    if actor_id:
        actor = db.query(ThreatActor).filter(ThreatActor.id == actor_id).first()
        if not actor:
            actor = ThreatActor(id=actor_id, actor_name=f"MockActor_{actor_id}")
            db.add(actor)
            db.commit()
    
    # Save Campaign
    campaign = APTCampaign(
        campaign_name=camp_name,
        threat_actor_id=actor_id,
        attribution_confidence=confidence,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    # Save TTPs and link to Campaign
    for tmap in ttp_maps:
        ttp = TTPMapping(
            campaign_id=campaign.id,
            technique_id=tmap["technique_id"],
            technique_name=tmap["technique_name"],
            graph_node_id=tmap["graph_node_id"],
            detection_score=tmap["detection_score"]
        )
        db.add(ttp)
        
    # Link Artifacts to Campaign
    for a in artifacts:
        a.campaign_id = campaign.id
        db.add(a)
        
    db.commit()
    db.refresh(campaign)
    return campaign

def get_threat_actors(db: Session) -> List[ThreatActor]:
    return db.query(ThreatActor).all()

from sqlalchemy.orm import Session
from ..models.campaignguard import DeepfakeCampaign, BotNetworkNode, OpinionImpact, TakedownRecommendation
from ..schemas.campaignguard import CampaignAnalyzeRequest, CampaignAnalysisResponse, DeepfakeCampaignRead, BotNetworkNodeRead, OpinionImpactRead, TakedownRecommendationRead
from ..modules.campaignguard_engine import track_propagation, detect_bot_amplification, assess_impact, generate_takedown_recommendations

def analyze_campaign(db: Session, request: CampaignAnalyzeRequest) -> CampaignAnalysisResponse:
    # 1. Track Propagation
    camp_data = track_propagation(request.media_url, request.target_entity)
    
    # Check if already tracked by hash
    campaign = db.query(DeepfakeCampaign).filter(DeepfakeCampaign.payload_hash == camp_data["payload_hash"]).first()
    if not campaign:
        campaign = DeepfakeCampaign(
            campaign_name=camp_data["campaign_name"],
            target_entity=camp_data["target_entity"],
            payload_hash=camp_data["payload_hash"],
            platforms_affected=camp_data["platforms_affected"]
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
    else:
        # If it exists, we just update the platforms if needed (mocking skipped for simplicity)
        pass

    # 2. Detect Bot Amplification
    bot_dicts = detect_bot_amplification(camp_data)
    saved_bots = []
    
    # Clear old bots for this demo flow
    db.query(BotNetworkNode).filter(BotNetworkNode.campaign_id == campaign.id).delete()
    
    for b_dict in bot_dicts:
        bot = BotNetworkNode(
            campaign_id=campaign.id,
            node_id=b_dict["node_id"],
            node_type=b_dict["node_type"],
            platform=b_dict["platform"],
            engagement_score=b_dict["engagement_score"]
        )
        db.add(bot)
        saved_bots.append(bot)
    db.commit()

    # Refresh bots to get IDs
    for bot in saved_bots:
        db.refresh(bot)

    # 3. Assess Impact
    impact_dict = assess_impact(camp_data, len(bot_dicts))
    impact = OpinionImpact(
        campaign_id=campaign.id,
        sentiment_drift=impact_dict["sentiment_drift"],
        reach_estimate=impact_dict["reach_estimate"],
        impact_score=impact_dict["impact_score"]
    )
    db.add(impact)
    db.commit()
    db.refresh(impact)

    # 4. Generate Recommendations
    rec_dicts = generate_takedown_recommendations(camp_data)
    saved_recs = []
    
    # Clear old recs for demo flow
    db.query(TakedownRecommendation).filter(TakedownRecommendation.campaign_id == campaign.id).delete()
    
    for r_dict in rec_dicts:
        rec = TakedownRecommendation(
            campaign_id=campaign.id,
            platform=r_dict["platform"],
            policy_violation=r_dict["policy_violation"],
            evidence_summary=r_dict["evidence_summary"],
            status=r_dict["status"]
        )
        db.add(rec)
        saved_recs.append(rec)
    db.commit()
    
    for rec in saved_recs:
        db.refresh(rec)

    return CampaignAnalysisResponse(
        campaign=DeepfakeCampaignRead.model_validate(campaign, from_attributes=True),
        bot_nodes=[BotNetworkNodeRead.model_validate(b, from_attributes=True) for b in saved_bots],
        impact=OpinionImpactRead.model_validate(impact, from_attributes=True),
        recommendations=[TakedownRecommendationRead.model_validate(r, from_attributes=True) for r in saved_recs]
    )

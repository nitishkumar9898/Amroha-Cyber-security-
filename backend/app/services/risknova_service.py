from sqlalchemy.orm import Session
from ..models.risknova import TechnologyProfile, RiskAssessment, RiskScenario, MitigationRoadmap
from ..schemas.risknova import AssessRequest, FullAssessmentResponse, TechnologyProfileRead, RiskAssessmentRead, RiskScenarioRead, MitigationRoadmapRead
from ..modules.risknova_engine import calculate_risk_score, forecast_scenarios, generate_mitigation_roadmap

def assess_emerging_tech(db: Session, request: AssessRequest) -> FullAssessmentResponse:
    # 1. Create or Update Tech Profile
    profile = db.query(TechnologyProfile).filter(TechnologyProfile.tech_name == request.tech_name).first()
    if not profile:
        profile = TechnologyProfile(
            tech_name=request.tech_name,
            sub_category=request.sub_category,
            adoption_phase=request.adoption_phase
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
    # 2. Calculate Risk Scores
    scores = calculate_risk_score({"tech_name": profile.tech_name, "adoption_phase": profile.adoption_phase})
    assessment = RiskAssessment(
        tech_id=profile.id,
        cyber_risk_score=scores["cyber_risk_score"],
        physical_risk_score=scores["physical_risk_score"],
        operational_risk_score=scores["operational_risk_score"],
        composite_score=scores["composite_score"]
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    # 3. Forecast Scenarios
    scenario_dicts = forecast_scenarios(profile.tech_name, scores)
    saved_scenarios = []
    saved_roadmaps = []
    
    for s_dict in scenario_dicts:
        scenario = RiskScenario(
            assessment_id=assessment.id,
            scenario_name=s_dict["scenario_name"],
            description=s_dict["description"],
            probability=s_dict["probability"],
            impact_level=s_dict["impact_level"],
            timeframe_years=s_dict["timeframe_years"]
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        saved_scenarios.append(scenario)
        
        # 4. Generate Roadmaps
        roadmap_dicts = generate_mitigation_roadmap(s_dict)
        for r_dict in roadmap_dicts:
            roadmap = MitigationRoadmap(
                scenario_id=scenario.id,
                step_order=r_dict["step_order"],
                action_item=r_dict["action_item"],
                resource_requirement=r_dict["resource_requirement"],
                status=r_dict["status"]
            )
            db.add(roadmap)
            db.commit()
            db.refresh(roadmap)
            saved_roadmaps.append(roadmap)
            
    # Serialize to Response
    return FullAssessmentResponse(
        profile=TechnologyProfileRead.model_validate(profile, from_attributes=True),
        assessment=RiskAssessmentRead.model_validate(assessment, from_attributes=True),
        scenarios=[RiskScenarioRead.model_validate(s, from_attributes=True) for s in saved_scenarios],
        roadmaps=[MitigationRoadmapRead.model_validate(r, from_attributes=True) for r in saved_roadmaps]
    )

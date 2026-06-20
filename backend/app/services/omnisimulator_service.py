import uuid
from sqlalchemy.orm import Session
from ..models.omnisimulator import GlobalScenario, ScenarioTimelineEvent, CrossModuleCascade
from ..schemas.omnisimulator import ScenarioCreateRequest, EventTriggerRequest
from ..modules.omnisimulator_engine import ScenarioDirector, CascadeEngine, OmniDefenseCoordinator

class OmniSimulatorService:
    @staticmethod
    def launch_scenario(db: Session, payload: ScenarioCreateRequest) -> dict:
        result = ScenarioDirector.create_scenario(payload.name)
        
        scenario = GlobalScenario(
            scenario_id=payload.scenario_id,
            name=payload.name,
            description=payload.description,
            active_modules_count=30, # We have 30 modules
            global_resilience_score=result["global_resilience_score"],
            status=result["status"]
        )
        db.add(scenario)
        db.commit()
        
        return {
            "scenario_id": payload.scenario_id,
            "name": payload.name,
            "status": result["status"],
            "global_resilience_score": result["global_resilience_score"]
        }

    @staticmethod
    def trigger_event(db: Session, payload: EventTriggerRequest) -> dict:
        event_id = f"EVT-{uuid.uuid4().hex[:6].upper()}"
        
        # 1. Log the initial event
        timeline_event = ScenarioTimelineEvent(
            scenario_id=payload.scenario_id,
            event_id=event_id,
            source_module=payload.source_module,
            event_description=payload.event_description,
            severity=payload.severity
        )
        db.add(timeline_event)
        
        # 2. Calculate Cascades
        cascades = CascadeEngine.calculate_cascades(payload.source_module, payload.severity)
        
        for c in cascades:
            cascade_record = CrossModuleCascade(
                scenario_id=payload.scenario_id,
                source_event_id=event_id,
                target_module=c["target_module"],
                cascade_probability=c["cascade_probability"],
                impact_description=c["impact_description"]
            )
            db.add(cascade_record)
            
        # 3. Update Global Resilience
        scenario = db.query(GlobalScenario).filter(GlobalScenario.scenario_id == payload.scenario_id).first()
        if scenario:
            new_score = OmniDefenseCoordinator.calculate_impact(scenario.global_resilience_score, cascades)
            scenario.global_resilience_score = new_score
        else:
            new_score = 100.0
            
        db.commit()
        
        return {
            "event_id": event_id,
            "source_module": payload.source_module,
            "event_description": payload.event_description,
            "cascades_triggered": len(cascades),
            "new_resilience_score": new_score
        }

    @staticmethod
    def get_global_state(db: Session, scenario_id: str) -> dict:
        scenario = db.query(GlobalScenario).filter(GlobalScenario.scenario_id == scenario_id).first()
        if not scenario:
            raise ValueError("Scenario not found")
            
        total_events = db.query(ScenarioTimelineEvent).filter(ScenarioTimelineEvent.scenario_id == scenario_id).count()
        total_cascades = db.query(CrossModuleCascade).filter(CrossModuleCascade.scenario_id == scenario_id).count()
        
        return {
            "scenario_id": scenario.scenario_id,
            "status": scenario.status,
            "global_resilience_score": scenario.global_resilience_score,
            "total_events": total_events,
            "total_cascades": total_cascades
        }

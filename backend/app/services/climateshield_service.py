from sqlalchemy.orm import Session
from ..models.climateshield import InfraAttackSim, ClimateManipulationSim, ResiliencePlan
from ..schemas.climateshield import InfraAttackRequest, ClimateSimRequest, ResiliencePlanRequest
from ..modules.climateshield_engine import InfraAttackModeler, ClimateManipulator, ResiliencePlanner

class ClimateShieldService:
    @staticmethod
    def simulate_infra_attack(db: Session, payload: InfraAttackRequest) -> dict:
        result = InfraAttackModeler.simulate(payload.infrastructure_type, payload.weather_event, payload.cyber_attack_vector)
        
        sim = InfraAttackSim(
            infrastructure_type=payload.infrastructure_type,
            weather_event=payload.weather_event,
            cyber_attack_vector=payload.cyber_attack_vector,
            cascading_impact_score=result["cascading_impact_score"]
        )
        db.add(sim)
        db.commit()
        
        return {
            "infrastructure_type": payload.infrastructure_type,
            "cascading_impact_score": result["cascading_impact_score"],
            "analysis_details": result["analysis_details"]
        }

    @staticmethod
    def simulate_climate_manipulation(db: Session, payload: ClimateSimRequest) -> dict:
        result = ClimateManipulator.simulate(payload.manipulation_vector, payload.projected_years)
        
        sim = ClimateManipulationSim(
            manipulation_vector=payload.manipulation_vector,
            projected_years=payload.projected_years,
            ecological_damage_index=result["ecological_damage_index"],
            economic_impact_trillions=result["economic_impact_trillions"]
        )
        db.add(sim)
        db.commit()
        
        return {
            "manipulation_vector": payload.manipulation_vector,
            "projected_years": payload.projected_years,
            "ecological_damage_index": result["ecological_damage_index"],
            "economic_impact_trillions": result["economic_impact_trillions"],
            "details": result["details"]
        }

    @staticmethod
    def generate_resilience_plan(db: Session, payload: ResiliencePlanRequest) -> dict:
        result = ResiliencePlanner.generate(payload.scenario_trigger, payload.severity_score)
        
        plan = ResiliencePlan(
            scenario_trigger=payload.scenario_trigger,
            recovery_strategy=result["recovery_strategy"],
            estimated_recovery_days=result["estimated_recovery_days"]
        )
        db.add(plan)
        db.commit()
        
        return {
            "scenario_trigger": payload.scenario_trigger,
            "recovery_strategy": result["recovery_strategy"],
            "estimated_recovery_days": result["estimated_recovery_days"]
        }

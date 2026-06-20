from sqlalchemy.orm import Session
from ..models.gridshield import ScadaAnomaly, CyberPhysicalSimulation, ResiliencePlan, ThreatForecast
from ..schemas.gridshield import ScadaAnalysisRequest, PhysicalSimulationRequest, ResiliencePlanRequest, ThreatForecastRequest
from ..modules.gridshield_engine import ScadaAnalyzer, PhysicalSimulator, ResiliencePlanner, ThreatForecaster

class GridShieldService:
    @staticmethod
    def analyze_scada(db: Session, payload: ScadaAnalysisRequest) -> dict:
        result = ScadaAnalyzer.analyze(payload.protocol, payload.packet_payload, payload.frequency_hz)
        
        anomaly = ScadaAnomaly(
            device_id=payload.device_id,
            protocol=payload.protocol,
            is_anomalous=result["is_anomalous"],
            flag_reason=result["flag_reason"]
        )
        db.add(anomaly)
        db.commit()
        
        return {
            "device_id": payload.device_id,
            "is_anomalous": result["is_anomalous"],
            "flag_reason": result["flag_reason"]
        }

    @staticmethod
    def simulate_physical(db: Session, payload: PhysicalSimulationRequest) -> dict:
        result = PhysicalSimulator.simulate(payload.injected_rpm, payload.normal_operating_rpm)
        
        simulation = CyberPhysicalSimulation(
            target_component=payload.target_component,
            injected_rpm=payload.injected_rpm,
            kinetic_damage_probability=result["kinetic_damage_probability"]
        )
        db.add(simulation)
        db.commit()
        
        return {
            "target_component": payload.target_component,
            "kinetic_damage_probability": result["kinetic_damage_probability"],
            "structural_integrity_warning": result["structural_integrity_warning"]
        }

    @staticmethod
    def plan_resilience(db: Session, payload: ResiliencePlanRequest) -> dict:
        result = ResiliencePlanner.plan(payload.current_load_mw, payload.compromised_nodes)
        
        plan = ResiliencePlan(
            grid_sector=payload.grid_sector,
            load_shedding_percentage=result["load_shedding_percentage"],
            islanding_required=result["islanding_required"]
        )
        db.add(plan)
        db.commit()
        
        return {
            "grid_sector": payload.grid_sector,
            "load_shedding_percentage": result["load_shedding_percentage"],
            "islanding_required": result["islanding_required"],
            "action_plan": result["action_plan"]
        }

    @staticmethod
    def forecast_threat(db: Session, payload: ThreatForecastRequest) -> dict:
        result = ThreatForecaster.forecast(payload.iot_integration_level, payload.past_incidents_count)
        
        forecast = ThreatForecast(
            region=payload.region,
            five_year_risk_score=result["five_year_risk_score"],
            primary_threat_vector=result["primary_threat_vector"]
        )
        db.add(forecast)
        db.commit()
        
        return {
            "region": payload.region,
            "five_year_risk_score": result["five_year_risk_score"],
            "primary_threat_vector": result["primary_threat_vector"]
        }

from sqlalchemy.orm import Session
from ..models.autoguard import VehicleLog, MalwareAlert, SwarmAttackScenario
from ..schemas.autoguard import VehicleLogCreate, SwarmScenarioCreate
from ..modules.autoguard_engine import parse_can_message, heuristic_malware_detection, simulate_swarm_attack
import json

def store_vehicle_log(db: Session, payload: VehicleLogCreate) -> VehicleLog:
    log = VehicleLog(
        vehicle_id=payload.vehicle_id,
        raw_data=payload.raw_data,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def run_malware_detection(db: Session, vehicle_id: str) -> MalwareAlert:
    # fetch latest log for vehicle
    log = db.query(VehicleLog).filter(VehicleLog.vehicle_id == vehicle_id).order_by(VehicleLog.timestamp.desc()).first()
    if not log:
        raise ValueError("No logs found for vehicle")
    messages = parse_can_message(log.raw_data)
    result = heuristic_malware_detection(messages)
    alert = MalwareAlert(
        vehicle_id=vehicle_id,
        signature_id=None,
        severity=result["severity"],
        description=result["description"],
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def run_swarm_simulation(db: Session, params: SwarmScenarioCreate):
    simulated = simulate_swarm_attack(**params.parameters)
    scenario = SwarmAttackScenario(
        scenario_name=simulated["scenario_name"],
        parameters=json.dumps(params.parameters),
        result=json.dumps({
            "generated_messages": simulated["generated_messages"],
            "timestamp": simulated["timestamp"]
        })
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario

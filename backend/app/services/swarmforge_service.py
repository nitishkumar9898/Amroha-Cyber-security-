from sqlalchemy.orm import Session
from ..models.swarmforge import SwarmSimulation, AgentMetrics, CounterSwarmDeployment
from ..schemas.swarmforge import SwarmSimRequest, CounterSwarmRequest
from ..modules.swarmforge_engine import MARLFramework, SwarmPredictor, CounterSwarmOrchestrator

class SwarmForgeService:
    @staticmethod
    def simulate_attack(db: Session, payload: SwarmSimRequest) -> dict:
        initial_coord = MARLFramework.initialize_swarm(payload.swarm_size)
        
        sim = SwarmSimulation(
            target_infrastructure=payload.target_infrastructure,
            swarm_size=payload.swarm_size,
            attack_vector=payload.attack_vector
        )
        db.add(sim)
        db.commit()
        db.refresh(sim)
        
        return {
            "simulation_id": sim.id,
            "status": "SWARM_DEPLOYED",
            "initial_coordination_score": initial_coord
        }

    @staticmethod
    def analyze_behavior(db: Session, simulation_id: int) -> dict:
        sim = db.query(SwarmSimulation).filter(SwarmSimulation.id == simulation_id).first()
        if not sim:
            raise ValueError("Simulation not found")
            
        metrics = MARLFramework.calculate_metrics()
        pivot = SwarmPredictor.predict_pivot(sim.target_infrastructure, metrics["mutation_velocity"])
        
        record = AgentMetrics(
            simulation_id=sim.id,
            coordination_score=metrics["coordination_score"],
            mutation_velocity=metrics["mutation_velocity"],
            predicted_pivot_target=pivot
        )
        db.add(record)
        db.commit()
        
        return {
            "simulation_id": sim.id,
            "coordination_score": metrics["coordination_score"],
            "mutation_velocity": metrics["mutation_velocity"],
            "predicted_pivot_target": pivot
        }

    @staticmethod
    def deploy_counter_swarm(db: Session, payload: CounterSwarmRequest) -> dict:
        sim = db.query(SwarmSimulation).filter(SwarmSimulation.id == payload.simulation_id).first()
        if not sim:
            raise ValueError("Simulation not found")
            
        # Get latest metrics or assume high coordination if none exist
        latest_metric = db.query(AgentMetrics).filter(AgentMetrics.simulation_id == sim.id).order_by(AgentMetrics.id.desc()).first()
        coord_score = latest_metric.coordination_score if latest_metric else 0.8
        
        result = CounterSwarmOrchestrator.deploy(payload.strategy_used, coord_score)
        
        deployment = CounterSwarmDeployment(
            simulation_id=sim.id,
            strategy_used=payload.strategy_used,
            neutralization_percentage=result["neutralization_percentage"]
        )
        db.add(deployment)
        
        if result["swarm_deactivated"]:
            sim.is_active = False
            
        db.commit()
        
        return {
            "simulation_id": sim.id,
            "strategy_used": payload.strategy_used,
            "neutralization_percentage": result["neutralization_percentage"],
            "swarm_deactivated": result["swarm_deactivated"]
        }

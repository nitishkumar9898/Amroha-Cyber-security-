import datetime
from sqlalchemy.orm import Session
from ..models.redteam import RedTeamScenario, SimulationRun, VulnerabilityFinding
from ..schemas.redteam import ScenarioCreate, SimulationStart, ActionSubmit
from ..modules.redteam_engine import AgenticScenarioGenerator, BlueVsRedSimulator, PostExerciseAnalyzer

# In-memory store for active simulations (maps run_id to BlueVsRedSimulator instance)
ACTIVE_SIMULATIONS = {}

class RedTeamService:
    
    @staticmethod
    def generate_scenario(db: Session, payload: ScenarioCreate) -> RedTeamScenario:
        graph = AgenticScenarioGenerator.generate(payload.name)
        
        scenario = RedTeamScenario(
            name=payload.name,
            description=payload.description,
            attack_graph=graph
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario

    @staticmethod
    def start_simulation(db: Session, payload: SimulationStart) -> SimulationRun:
        scenario = db.query(RedTeamScenario).filter(RedTeamScenario.id == payload.scenario_id).first()
        if not scenario:
            raise ValueError("Scenario not found")
            
        run = SimulationRun(
            scenario_id=scenario.id,
            status="IN_PROGRESS",
            metrics={"red_progress": 0, "blue_defenses_deployed": 0}
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # Initialize simulator instance in memory
        ACTIVE_SIMULATIONS[run.id] = BlueVsRedSimulator(scenario.attack_graph)
        
        return run

    @staticmethod
    def submit_action(db: Session, run_id: int, payload: ActionSubmit) -> dict:
        run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
        if not run:
            raise ValueError("Simulation run not found")
            
        simulator = ACTIVE_SIMULATIONS.get(run_id)
        if not simulator:
            raise ValueError("Simulation is not active in memory")
            
        result = simulator.apply_action(payload.team, payload.action_type, payload.target)
        
        # Update metrics
        run.metrics = {
            "red_progress": simulator.red_progress,
            "blue_defenses_deployed": simulator.blue_defenses_deployed
        }
        
        # Check if simulation ended
        if simulator.state in ["red_win", "blue_win"]:
            run.status = "COMPLETED"
            run.completed_at = datetime.datetime.utcnow()
            # Clean up memory
            if run_id in ACTIVE_SIMULATIONS:
                del ACTIVE_SIMULATIONS[run_id]
                
        db.commit()
        return {"action_result": result, "simulation_state": simulator.state}

    @staticmethod
    def get_analysis(db: Session, run_id: int) -> dict:
        run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
        if not run:
            raise ValueError("Simulation run not found")
            
        if run.status != "COMPLETED":
            raise ValueError("Simulation must be completed to generate an analysis report")
            
        recommendations = PostExerciseAnalyzer.analyze(run.metrics or {})
        
        findings_count = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.run_id == run_id).count()
        
        return {
            "run_id": run.id,
            "status": run.status,
            "total_vulnerabilities_found": findings_count,
            "recommendations": recommendations,
            "metrics": run.metrics
        }

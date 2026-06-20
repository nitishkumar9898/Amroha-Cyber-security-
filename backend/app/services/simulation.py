"""
Simulation Management Service
Handles scenario creation, phase tracking, and coordinates file generation.
"""

from sqlalchemy.orm import Session
from ..models import DBScenarioRun
from ..schemas import ScenarioCreate
from datetime import datetime

class SimulationService:
    @staticmethod
    def get_runs(db: Session):
        return db.query(DBScenarioRun).all()

    @staticmethod
    def create_run(db: Session, run_in: ScenarioCreate):
        db_run = DBScenarioRun(
            scenario_id=run_in.scenario_id,
            name=run_in.name,
            threat_actor=run_in.threat_actor,
            target_sector=run_in.target_sector,
            status="RUNNING",
            start_time=datetime.utcnow(),
            completed_phases=""
        )
        db.add(db_run)
        db.commit()
        db.refresh(db_run)
        return db_run

    @staticmethod
    def update_phase(db: Session, run_id: int, phase_name: str):
        db_run = db.query(DBScenarioRun).filter(DBScenarioRun.id == run_id).first()
        if not db_run:
            return None
        
        phases = [p.strip() for p in db_run.completed_phases.split(",") if p.strip()]
        if phase_name not in phases:
            phases.append(phase_name)
            db_run.completed_phases = ",".join(phases)
            
            # Simple check if all four core phases completed
            if len(phases) >= 4:
                db_run.status = "COMPLETED"
            
            db.commit()
            db.refresh(db_run)
        return db_run

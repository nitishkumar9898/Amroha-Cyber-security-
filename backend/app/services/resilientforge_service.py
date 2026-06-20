from sqlalchemy.orm import Session
from ..models.resilientforge import DisasterSimulation, BackupIntegrityLog, SelfHealingEvent
from ..schemas.resilientforge import SimulationRequest, BackupVerifyRequest, HealRequest
from ..modules.resilientforge_engine import DisasterSimulator, BackupVerifier, AutoHealer

class ResilientForgeService:
    @staticmethod
    def simulate_disaster(db: Session, payload: SimulationRequest) -> dict:
        result = DisasterSimulator.simulate(payload.scenario_name, payload.simulated_downtime_hours)
        
        sim_record = DisasterSimulation(
            scenario_name=payload.scenario_name,
            target_infrastructure=payload.target_infrastructure,
            simulated_downtime_hours=payload.simulated_downtime_hours,
            optimized_rto_hours=result["optimized_rto_hours"]
        )
        db.add(sim_record)
        db.commit()
        
        return {
            "scenario_name": payload.scenario_name,
            "target_infrastructure": payload.target_infrastructure,
            "optimized_rto_hours": result["optimized_rto_hours"],
            "optimization_strategy": result["optimization_strategy"]
        }

    @staticmethod
    def verify_backup(db: Session, payload: BackupVerifyRequest) -> dict:
        result = BackupVerifier.verify(payload.file_signature)
        
        log_record = BackupIntegrityLog(
            backup_id=payload.backup_id,
            file_signature=payload.file_signature,
            is_corrupt=result["is_corrupt"],
            malware_detected=result["malware_detected"]
        )
        db.add(log_record)
        db.commit()
        
        return {
            "backup_id": payload.backup_id,
            "is_corrupt": result["is_corrupt"],
            "malware_detected": result["malware_detected"],
            "status_message": result["status_message"]
        }

    @staticmethod
    def trigger_heal(db: Session, payload: HealRequest) -> dict:
        result = AutoHealer.heal(payload.initial_state)
        
        heal_record = SelfHealingEvent(
            asset_id=payload.asset_id,
            initial_state=payload.initial_state,
            final_state=result["final_state"],
            reconstruction_method=result["reconstruction_method"]
        )
        db.add(heal_record)
        db.commit()
        
        # Integration hook: We could trigger ResponseForge here
        
        return {
            "asset_id": payload.asset_id,
            "final_state": result["final_state"],
            "reconstruction_method": result["reconstruction_method"]
        }

from sqlalchemy.orm import Session
from ..models.metaforge import PlatformMetric, EvolutionLog, InternalAnomaly
from ..schemas.metaforge import MetricIngestRequest, EvolutionRequest, InternalAnomalyRequest
from ..modules.metaforge_engine import PlatformMonitor, EvolutionManager, AnomalyDetector

class MetaForgeService:
    @staticmethod
    def ingest_metric(db: Session, payload: MetricIngestRequest) -> dict:
        result = PlatformMonitor.analyze(payload.source_module, payload.latency_ms, payload.error_rate)
        
        metric = PlatformMetric(
            source_module=payload.source_module,
            latency_ms=payload.latency_ms,
            error_rate=payload.error_rate,
            optimization_suggestion=result["optimization_suggestion"]
        )
        db.add(metric)
        db.commit()
        
        return {
            "source_module": payload.source_module,
            "optimization_suggestion": result["optimization_suggestion"]
        }

    @staticmethod
    def manage_evolution(db: Session, payload: EvolutionRequest) -> dict:
        result = EvolutionManager.manage(payload.target_module, payload.current_version)
        
        log = EvolutionLog(
            target_module=payload.target_module,
            current_version=payload.current_version,
            proposed_version=result["proposed_version"],
            upgrade_manifest=result["upgrade_manifest"]
        )
        db.add(log)
        db.commit()
        
        return {
            "target_module": payload.target_module,
            "proposed_version": result["proposed_version"],
            "upgrade_manifest": result["upgrade_manifest"]
        }

    @staticmethod
    def detect_anomaly(db: Session, payload: InternalAnomalyRequest) -> dict:
        result = AnomalyDetector.detect(payload.subsystem, payload.anomaly_type)
        
        anomaly = InternalAnomaly(
            subsystem=payload.subsystem,
            anomaly_type=payload.anomaly_type,
            severity=result["severity"],
            action_taken=result["action_taken"]
        )
        db.add(anomaly)
        db.commit()
        
        return {
            "subsystem": payload.subsystem,
            "severity": result["severity"],
            "action_taken": result["action_taken"]
        }

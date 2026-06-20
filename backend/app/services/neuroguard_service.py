from sqlalchemy.orm import Session
from ..models.neuroguard import NeuralScan, BCIHackSimulation, NeuralPrivacyLog
from ..schemas.neuroguard import NeuralTelemetryRequest, BCISimRequest, PrivacyEnforcementRequest
from ..modules.neuroguard_engine import NeuralSignalAnalyzer, BCISimulator, PrivacyEnforcer

class NeuroGuardService:
    @staticmethod
    def analyze_telemetry(db: Session, payload: NeuralTelemetryRequest) -> dict:
        result = NeuralSignalAnalyzer.analyze(payload.alpha_band_hz, payload.beta_band_hz, payload.gamma_band_hz)
        
        scan = NeuralScan(
            subject_id=payload.subject_id,
            alpha_band_hz=payload.alpha_band_hz,
            beta_band_hz=payload.beta_band_hz,
            gamma_band_hz=payload.gamma_band_hz,
            is_anomalous=result["is_anomalous"],
            anomaly_type=result["anomaly_type"]
        )
        db.add(scan)
        db.commit()
        
        return {
            "subject_id": payload.subject_id,
            "is_anomalous": result["is_anomalous"],
            "anomaly_type": result["anomaly_type"],
            "status_message": result["status_message"]
        }

    @staticmethod
    def simulate_bci_hack(db: Session, payload: BCISimRequest) -> dict:
        result = BCISimulator.simulate(payload.attack_vector)
        
        sim = BCIHackSimulation(
            attack_vector=payload.attack_vector,
            biological_impact=result["biological_impact"],
            countermeasure_deployed=result["countermeasure_deployed"]
        )
        db.add(sim)
        db.commit()
        
        return {
            "attack_vector": payload.attack_vector,
            "biological_impact": result["biological_impact"],
            "countermeasure_deployed": result["countermeasure_deployed"]
        }

    @staticmethod
    def enforce_privacy(db: Session, payload: PrivacyEnforcementRequest) -> dict:
        result = PrivacyEnforcer.enforce(payload.raw_thought_data)
        
        log = NeuralPrivacyLog(
            data_packet_id=payload.data_packet_id,
            encryption_standard=result["encryption_standard"],
            is_secure=result["is_secure"]
        )
        db.add(log)
        db.commit()
        
        return {
            "data_packet_id": payload.data_packet_id,
            "is_secure": result["is_secure"],
            "encryption_standard": result["encryption_standard"],
            "message": result["message"]
        }

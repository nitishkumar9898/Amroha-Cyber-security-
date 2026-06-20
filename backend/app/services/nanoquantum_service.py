from sqlalchemy.orm import Session
from ..models.nanoquantum import NanoDeviceScan, NanoThreatSim, QuantumHardwareValidation
from ..schemas.nanoquantum import NanoScanRequest, NanoSimRequest, HardwareValidationRequest
from ..modules.nanoquantum_engine import NanoSensorAnalyzer, NanoThreatSimulator, HardwareValidator

class NanoQuantumService:
    @staticmethod
    def analyze_sensor(db: Session, payload: NanoScanRequest) -> dict:
        result = NanoSensorAnalyzer.analyze(payload.electron_spin_variance, payload.entanglement_stable)
        
        scan = NanoDeviceScan(
            device_id=payload.device_id,
            electron_spin_variance=payload.electron_spin_variance,
            entanglement_stable=payload.entanglement_stable,
            is_hijacked=result["is_hijacked"]
        )
        db.add(scan)
        db.commit()
        
        return {
            "device_id": payload.device_id,
            "is_hijacked": result["is_hijacked"],
            "status_message": result["status_message"]
        }

    @staticmethod
    def simulate_nano_threat(db: Session, payload: NanoSimRequest) -> dict:
        result = NanoThreatSimulator.simulate(payload.threat_type, payload.time_elapsed_seconds)
        
        sim = NanoThreatSim(
            threat_type=payload.threat_type,
            replication_rate=result["replication_rate"],
            material_consumed_kg=result["material_consumed_kg"],
            countermeasure_deployed=result["countermeasure_deployed"]
        )
        db.add(sim)
        db.commit()
        
        return {
            "threat_type": payload.threat_type,
            "replication_rate": result["replication_rate"],
            "material_consumed_kg": result["material_consumed_kg"],
            "countermeasure_deployed": result["countermeasure_deployed"]
        }

    @staticmethod
    def validate_hardware(db: Session, payload: HardwareValidationRequest) -> dict:
        result = HardwareValidator.validate(payload.pqc_algorithm_applied)
        
        validation = QuantumHardwareValidation(
            hardware_id=payload.hardware_id,
            pqc_algorithm_applied=payload.pqc_algorithm_applied,
            atomic_integrity_verified=result["atomic_integrity_verified"]
        )
        db.add(validation)
        db.commit()
        
        return {
            "hardware_id": payload.hardware_id,
            "atomic_integrity_verified": result["atomic_integrity_verified"],
            "message": result["message"]
        }

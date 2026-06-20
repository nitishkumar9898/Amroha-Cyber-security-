from sqlalchemy.orm import Session
from ..models.droneguard import TelemetryAnalysis, DroneMalware, SwarmAttack, AerialEvidence
from ..schemas.droneguard import TelemetryRequest, MalwareAnalysisRequest, SwarmSimulationRequest, EvidenceComplianceRequest
from ..modules.droneguard_engine import TelemetryAnalyzer, MalwareReverseEngineer, SwarmSimulator, ComplianceManager

class DroneGuardService:
    @staticmethod
    def analyze_telemetry(db: Session, payload: TelemetryRequest) -> dict:
        result = TelemetryAnalyzer.analyze(payload.gps_lat, payload.gps_lon, payload.ins_lat, payload.ins_lon)
        
        telemetry = TelemetryAnalysis(
            drone_id=payload.drone_id,
            gps_variance_meters=result["gps_variance_meters"],
            is_spoofed=result["is_spoofed"]
        )
        db.add(telemetry)
        db.commit()
        
        return {
            "drone_id": payload.drone_id,
            "gps_variance_meters": result["gps_variance_meters"],
            "is_spoofed": result["is_spoofed"],
            "action_taken": result["action_taken"]
        }

    @staticmethod
    def analyze_malware(db: Session, payload: MalwareAnalysisRequest) -> dict:
        result = MalwareReverseEngineer.analyze(payload.firmware_hash)
        
        malware = DroneMalware(
            firmware_hash=payload.firmware_hash,
            malware_family=result["malware_family"],
            payload_extracted=result["payload_extracted"]
        )
        db.add(malware)
        db.commit()
        
        return {
            "firmware_hash": payload.firmware_hash,
            "malware_family": result["malware_family"],
            "payload_extracted": result["payload_extracted"]
        }

    @staticmethod
    def simulate_swarm(db: Session, payload: SwarmSimulationRequest) -> dict:
        result = SwarmSimulator.simulate(payload.drone_count, payload.formation_type)
        
        swarm = SwarmAttack(
            swarm_id=payload.swarm_id,
            drone_count=payload.drone_count,
            formation_type=payload.formation_type,
            saturation_level=result["saturation_level"]
        )
        db.add(swarm)
        db.commit()
        
        return {
            "swarm_id": payload.swarm_id,
            "saturation_level": result["saturation_level"],
            "threat_assessment": result["threat_assessment"]
        }

    @staticmethod
    def secure_evidence(db: Session, payload: EvidenceComplianceRequest) -> dict:
        result = ComplianceManager.secure(payload.raw_data)
        
        evidence = AerialEvidence(
            case_id=payload.case_id,
            file_name=payload.file_name,
            sha256_hash=result["sha256_hash"],
            is_compliant=result["is_compliant"]
        )
        db.add(evidence)
        db.commit()
        
        return {
            "case_id": payload.case_id,
            "file_name": payload.file_name,
            "sha256_hash": result["sha256_hash"],
            "is_compliant": result["is_compliant"]
        }

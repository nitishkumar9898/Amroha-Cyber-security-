from sqlalchemy.orm import Session
from ..models.spaceguard import SatCommLog, OrbitalSupplyChainSim, SpaceAssetStrategy
from ..schemas.spaceguard import SatCommRequest, OrbitalSimRequest, AssetProtectionRequest
from ..modules.spaceguard_engine import SatProtocolAnalyzer, OrbitalSimEngine, AssetProtector

class SpaceGuardService:
    @staticmethod
    def analyze_sat_comm(db: Session, payload: SatCommRequest) -> dict:
        result = SatProtocolAnalyzer.analyze(payload.signal_to_noise_ratio, payload.auth_handshake_valid)
        
        log = SatCommLog(
            satellite_id=payload.satellite_id,
            protocol=payload.protocol,
            signal_to_noise_ratio=payload.signal_to_noise_ratio,
            auth_handshake_valid=payload.auth_handshake_valid,
            is_hijacked=result["is_hijacked"]
        )
        db.add(log)
        db.commit()
        
        return {
            "satellite_id": payload.satellite_id,
            "is_hijacked": result["is_hijacked"],
            "status_message": result["status_message"]
        }

    @staticmethod
    def simulate_orbital_attack(db: Session, payload: OrbitalSimRequest) -> dict:
        result = OrbitalSimEngine.simulate(payload.firmware_hash)
        
        sim = OrbitalSupplyChainSim(
            mission_name=payload.mission_name,
            payload_type=payload.payload_type,
            firmware_hash=payload.firmware_hash,
            orbital_risk_score=result["orbital_risk_score"],
            vulnerability_found=result["vulnerability_found"]
        )
        db.add(sim)
        db.commit()
        
        return {
            "mission_name": payload.mission_name,
            "orbital_risk_score": result["orbital_risk_score"],
            "vulnerability_found": result["vulnerability_found"],
            "details": result["details"]
        }

    @staticmethod
    def protect_asset(db: Session, payload: AssetProtectionRequest) -> dict:
        posture = AssetProtector.protect(payload.threat_intel_level)
        
        strategy = SpaceAssetStrategy(
            asset_id=payload.asset_id,
            threat_intel_level=payload.threat_intel_level,
            defensive_posture=posture
        )
        db.add(strategy)
        db.commit()
        
        return {
            "asset_id": payload.asset_id,
            "defensive_posture": posture
        }

from sqlalchemy.orm import Session
from ..models.metaguard import VirtualAssetTransaction, AvatarBehavior, CrimeCorrelation, VirtualEvidence
from ..schemas.metaguard import AssetTrackingRequest, AvatarBehaviorRequest, CrimeCorrelationRequest, EvidenceVisualizationRequest
from ..modules.metaguard_engine import AssetTracker, BehaviorAnalyzer, CorrelationEngine, ImmersiveVisualizer

class MetaGuardService:
    @staticmethod
    def track_asset(db: Session, payload: AssetTrackingRequest) -> dict:
        result = AssetTracker.track(payload.wallet_hops, payload.time_window_seconds)
        
        transaction = VirtualAssetTransaction(
            asset_id=payload.asset_id,
            wallet_hops=payload.wallet_hops,
            time_window_seconds=payload.time_window_seconds,
            is_laundering_risk=result["is_laundering_risk"]
        )
        db.add(transaction)
        db.commit()
        
        return {
            "asset_id": payload.asset_id,
            "is_laundering_risk": result["is_laundering_risk"],
            "action_taken": result["action_taken"]
        }

    @staticmethod
    def analyze_avatar(db: Session, payload: AvatarBehaviorRequest) -> dict:
        result = BehaviorAnalyzer.analyze(payload.kinematic_jitter, payload.manipulative_language)
        
        behavior = AvatarBehavior(
            avatar_id=payload.avatar_id,
            kinematic_jitter=payload.kinematic_jitter,
            manipulative_language=payload.manipulative_language,
            social_engineering_risk=result["social_engineering_risk"]
        )
        db.add(behavior)
        db.commit()
        
        return {
            "avatar_id": payload.avatar_id,
            "social_engineering_risk": result["social_engineering_risk"],
            "risk_assessment": result["risk_assessment"]
        }

    @staticmethod
    def correlate_crime(db: Session, payload: CrimeCorrelationRequest) -> dict:
        result = CorrelationEngine.correlate(payload.virtual_ip_log)
        
        correlation = CrimeCorrelation(
            virtual_incident_id=payload.virtual_incident_id,
            hardware_id_hash=result["hardware_id_hash"],
            physical_location_estimate=result["physical_location_estimate"]
        )
        db.add(correlation)
        db.commit()
        
        return {
            "virtual_incident_id": payload.virtual_incident_id,
            "hardware_id_hash": result["hardware_id_hash"],
            "physical_location_estimate": result["physical_location_estimate"]
        }

    @staticmethod
    def visualize_evidence(db: Session, payload: EvidenceVisualizationRequest) -> dict:
        result = ImmersiveVisualizer.generate_manifest(payload.scene_id, payload.raw_spatial_data)
        
        evidence = VirtualEvidence(
            scene_id=payload.scene_id,
            manifest_url=result["manifest_url"],
            is_training_ready=result["is_training_ready"]
        )
        db.add(evidence)
        db.commit()
        
        return {
            "scene_id": payload.scene_id,
            "manifest_url": result["manifest_url"],
            "is_training_ready": result["is_training_ready"]
        }

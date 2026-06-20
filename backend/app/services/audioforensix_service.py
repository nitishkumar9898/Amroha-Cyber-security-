from sqlalchemy.orm import Session
from ..models.audioforensix import AudioSample, VoiceBiometricProfile, SpectrogramAnalysis, AcousticEnvironment
from ..schemas.audioforensix import (
    AudioIngestRequest, DeepfakeDetectionRequest, EnvironmentReconstructionRequest
)
from ..modules.audioforensix_engine import VoiceBiometricsAnalyzer, SpectrogramDeepfakeDetector, AcousticReconstructor

class AudioForensixService:
    @staticmethod
    def ingest_audio(db: Session, payload: AudioIngestRequest) -> dict:
        sample = AudioSample(
            sample_id=payload.sample_id,
            filename=payload.filename,
            duration_seconds=payload.duration_seconds,
            format=payload.format
        )
        db.add(sample)
        db.commit()
        return {
            "sample_id": payload.sample_id,
            "status": "INGESTED"
        }

    @staticmethod
    def detect_deepfake(db: Session, payload: DeepfakeDetectionRequest) -> dict:
        # 1. Voice Biometrics
        bio_result = VoiceBiometricsAnalyzer.analyze(payload.claimed_identity)
        bio_profile = VoiceBiometricProfile(
            sample_id=payload.sample_id,
            claimed_identity=payload.claimed_identity,
            match_confidence=bio_result["match_confidence"],
            liveness_score=bio_result["liveness_score"],
            is_spoofed=bio_result["is_spoofed"]
        )
        db.add(bio_profile)
        
        # 2. Spectrogram Analysis
        spec_result = SpectrogramDeepfakeDetector.detect()
        spec_profile = SpectrogramAnalysis(
            sample_id=payload.sample_id,
            high_freq_artifacts=spec_result["high_freq_artifacts"],
            phase_irregularities=spec_result["phase_irregularities"],
            ai_probability=spec_result["ai_probability"],
            is_deepfake=spec_result["is_deepfake"]
        )
        db.add(spec_profile)
        
        db.commit()
        
        return {
            "sample_id": payload.sample_id,
            "claimed_identity": payload.claimed_identity,
            "match_confidence": bio_result["match_confidence"],
            "liveness_score": bio_result["liveness_score"],
            "is_spoofed": bio_result["is_spoofed"],
            "high_freq_artifacts": spec_result["high_freq_artifacts"],
            "ai_probability": spec_result["ai_probability"],
            "is_deepfake": spec_result["is_deepfake"]
        }

    @staticmethod
    def reconstruct_environment(db: Session, payload: EnvironmentReconstructionRequest) -> dict:
        env_result = AcousticReconstructor.reconstruct()
        
        env_profile = AcousticEnvironment(
            sample_id=payload.sample_id,
            rt60_decay=env_result["rt60_decay"],
            background_noise_profile=env_result["background_noise_profile"],
            estimated_environment=env_result["estimated_environment"]
        )
        db.add(env_profile)
        db.commit()
        
        return {
            "sample_id": payload.sample_id,
            "rt60_decay": env_result["rt60_decay"],
            "background_noise_profile": env_result["background_noise_profile"],
            "estimated_environment": env_result["estimated_environment"]
        }

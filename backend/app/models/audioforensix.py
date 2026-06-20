from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class AudioSample(Base):
    __tablename__ = "audioforensix_samples"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(String, index=True, unique=True)
    filename = Column(String)
    duration_seconds = Column(Float)
    format = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

class VoiceBiometricProfile(Base):
    __tablename__ = "audioforensix_biometrics"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(String, index=True)
    claimed_identity = Column(String)
    match_confidence = Column(Float)
    liveness_score = Column(Float)
    is_spoofed = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class SpectrogramAnalysis(Base):
    __tablename__ = "audioforensix_spectrograms"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(String, index=True)
    high_freq_artifacts = Column(Float)
    phase_irregularities = Column(Float)
    ai_probability = Column(Float)
    is_deepfake = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class AcousticEnvironment(Base):
    __tablename__ = "audioforensix_environments"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(String, index=True)
    rt60_decay = Column(Float)
    background_noise_profile = Column(String)
    estimated_environment = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

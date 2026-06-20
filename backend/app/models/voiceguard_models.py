from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class AudioForensicsTask(Base):
    __tablename__ = "voiceguard_tasks"
    id = Column(Integer, primary_key=True, index=True)
    audio_file_hash = Column(String)
    speaker_id = Column(String)
    synthetic_probability = Column(Float, default=0.0)
    spectral_anomalies = Column(String)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

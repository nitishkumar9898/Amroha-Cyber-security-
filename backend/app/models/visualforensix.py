from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class MediaAsset(Base):
    __tablename__ = "visualforensix_media"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String, index=True, unique=True)
    filename = Column(String)
    media_type = Column(String) # image or video
    file_size_kb = Column(Float)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

class PixelForgeryAnalysis(Base):
    __tablename__ = "visualforensix_pixel_analysis"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String, index=True)
    ela_score = Column(Float) # Error Level Analysis anomaly score
    double_compression_detected = Column(Boolean)
    is_tampered = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class DeepfakeVideoAnalysis(Base):
    __tablename__ = "visualforensix_video_analysis"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String, index=True)
    temporal_inconsistency = Column(Float)
    face_warp_artifacts = Column(Float)
    is_deepfake = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class ForensicReport(Base):
    __tablename__ = "visualforensix_reports"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String, index=True)
    report_hash = Column(String)
    admissibility_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

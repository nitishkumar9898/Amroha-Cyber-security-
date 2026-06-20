from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

class MediaIngestRequest(BaseModel):
    asset_id: str
    filename: str
    media_type: str
    file_size_kb: float

class MediaIngestResult(BaseModel):
    asset_id: str
    status: str

class VisualAnalysisRequest(BaseModel):
    asset_id: str
    media_type: str # "image" or "video"

class PixelAnalysisResult(BaseModel):
    ela_score: float
    double_compression_detected: bool
    is_tampered: bool

class VideoAnalysisResult(BaseModel):
    temporal_inconsistency: float
    face_warp_artifacts: float
    is_deepfake: bool

class VisualAnalysisResult(BaseModel):
    asset_id: str
    pixel_analysis: Optional[PixelAnalysisResult] = None
    video_analysis: Optional[VideoAnalysisResult] = None
    metadata_anomalies: int

class ReportGenerationRequest(BaseModel):
    asset_id: str
    pixel_analysis: Optional[Dict[str, Any]] = None
    video_analysis: Optional[Dict[str, Any]] = None

class ReportGenerationResult(BaseModel):
    asset_id: str
    report_hash: str
    admissibility_score: float
    report_data: Dict[str, Any]

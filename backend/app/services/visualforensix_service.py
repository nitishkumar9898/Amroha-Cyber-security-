from sqlalchemy.orm import Session
from ..models.visualforensix import MediaAsset, PixelForgeryAnalysis, DeepfakeVideoAnalysis, ForensicReport
from ..schemas.visualforensix import (
    MediaIngestRequest, VisualAnalysisRequest, ReportGenerationRequest
)
from ..modules.visualforensix_engine import PixelForgeryDetector, DeepfakeVideoDetector, MetadataAnalyzer, ReportGenerator

class VisualForensixService:
    @staticmethod
    def ingest_media(db: Session, payload: MediaIngestRequest) -> dict:
        asset = MediaAsset(
            asset_id=payload.asset_id,
            filename=payload.filename,
            media_type=payload.media_type,
            file_size_kb=payload.file_size_kb
        )
        db.add(asset)
        db.commit()
        return {"asset_id": payload.asset_id, "status": "INGESTED"}

    @staticmethod
    def analyze_media(db: Session, payload: VisualAnalysisRequest) -> dict:
        metadata_anomalies = MetadataAnalyzer.detect_anomalies()
        
        result = {
            "asset_id": payload.asset_id,
            "metadata_anomalies": metadata_anomalies,
            "pixel_analysis": None,
            "video_analysis": None
        }

        if payload.media_type == "image":
            pixel_data = PixelForgeryDetector.detect()
            analysis_record = PixelForgeryAnalysis(
                asset_id=payload.asset_id,
                ela_score=pixel_data["ela_score"],
                double_compression_detected=pixel_data["double_compression_detected"],
                is_tampered=pixel_data["is_tampered"]
            )
            db.add(analysis_record)
            result["pixel_analysis"] = pixel_data

        elif payload.media_type == "video":
            video_data = DeepfakeVideoDetector.detect()
            analysis_record = DeepfakeVideoAnalysis(
                asset_id=payload.asset_id,
                temporal_inconsistency=video_data["temporal_inconsistency"],
                face_warp_artifacts=video_data["face_warp_artifacts"],
                is_deepfake=video_data["is_deepfake"]
            )
            db.add(analysis_record)
            result["video_analysis"] = video_data

        db.commit()
        return result

    @staticmethod
    def generate_report(db: Session, payload: ReportGenerationRequest) -> dict:
        report_data = ReportGenerator.generate(
            payload.asset_id, 
            payload.pixel_analysis, 
            payload.video_analysis
        )
        
        report_record = ForensicReport(
            asset_id=payload.asset_id,
            report_hash=report_data["report_hash"],
            admissibility_score=report_data["admissibility_score"]
        )
        db.add(report_record)
        db.commit()
        
        return report_data

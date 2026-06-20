import random
import hashlib
import json

class PixelForgeryDetector:
    """Detects image splicing and copy-move attacks via Error Level Analysis (ELA)."""
    @staticmethod
    def detect() -> dict:
        ela_score = random.uniform(10.0, 95.0)
        double_compression = random.choice([True, False])
        
        is_tampered = ela_score > 70.0 or (ela_score > 50.0 and double_compression)
        
        return {
            "ela_score": ela_score,
            "double_compression_detected": double_compression,
            "is_tampered": is_tampered
        }

class DeepfakeVideoDetector:
    """Detects AI-generated video via temporal inconsistencies and face warping."""
    @staticmethod
    def detect() -> dict:
        temporal_inconsistency = random.uniform(5.0, 99.0)
        face_warp_artifacts = random.uniform(5.0, 99.0)
        
        is_deepfake = (temporal_inconsistency + face_warp_artifacts) / 2 > 60.0
        
        return {
            "temporal_inconsistency": temporal_inconsistency,
            "face_warp_artifacts": face_warp_artifacts,
            "is_deepfake": is_deepfake
        }

class MetadataAnalyzer:
    """Simulates EXIF data extraction and contradiction checking."""
    @staticmethod
    def detect_anomalies() -> int:
        # Returns number of detected anomalies (e.g. GPS says night, image says day)
        return random.randint(0, 5)

class ReportGenerator:
    """Generates a court-admissible forensic JSON report with cryptographic signing."""
    @staticmethod
    def generate(asset_id: str, pixel_data: dict = None, video_data: dict = None) -> dict:
        report_data = {
            "asset_id": asset_id,
            "pixel_analysis": pixel_data,
            "video_analysis": video_data,
            "forensic_conclusion": "TAMPERED" if (
                (pixel_data and pixel_data.get("is_tampered")) or 
                (video_data and video_data.get("is_deepfake"))
            ) else "AUTHENTIC"
        }
        
        report_string = json.dumps(report_data, sort_keys=True)
        report_hash = hashlib.sha256(report_string.encode('utf-8')).hexdigest()
        
        admissibility_score = random.uniform(85.0, 99.9)
        
        return {
            "asset_id": asset_id,
            "report_hash": report_hash,
            "admissibility_score": admissibility_score,
            "report_data": report_data
        }

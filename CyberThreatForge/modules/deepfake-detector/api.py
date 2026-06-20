"""FastAPI application for multi-modal deepfake & misinformation detection.

Endpoints:
  - POST /analyze/video   — Video deepfake analysis (frame, lip-sync, bio signals)
  - POST /analyze/audio   — Audio deepfake analysis (spectrogram, voice fingerprint)
  - POST /analyze/image   — Image deepfake analysis (ELA, PRNU, metadata, GAN fingerprint)
  - POST /analyze/text    — Text misinformation analysis (perplexity, watermark, stylometry)
  - GET  /health          — Health check with model load status
"""

import io
import os
import json
import time
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Any, Optional
from contextlib import asynccontextmanager

import torch
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from models.mesonet import Meso4, MesoInception4
from models.xception_fingerprint import XceptionFingerprint
from pipelines.video_pipeline import VideoPipeline
from pipelines.audio_pipeline import AudioPipeline
from pipelines.text_pipeline import TextPipeline

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ProgressUpdate(BaseModel):
    percent: int = Field(..., ge=0, le=100)
    stage: str

class HealthResponse(BaseModel):
    status: str
    device: str
    models_loaded: dict[str, bool]
    cuda_available: bool
    version: str = "1.0.0"

class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    results: dict[str, Any]
    processing_time_ms: float
    chain_of_custody: list[dict[str, Any]]

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    job_id: Optional[str] = None

class EnsembleFusionResult(BaseModel):
    final_score: float
    is_deepfake: bool
    modality_contributions: dict[str, float]

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

class Models:
    meso4: Optional[Meso4] = None
    meso_inception: Optional[MesoInception4] = None
    xception: Optional[XceptionFingerprint] = None

    @classmethod
    def status(cls) -> dict[str, bool]:
        return {
            "meso4": cls.meso4 is not None,
            "meso_inception": cls.meso_inception is not None,
            "xception_fingerprint": cls.xception is not None,
        }

models = Models()
device: torch.device = torch.device("cpu")

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    try:
        models.meso4 = Meso4(num_classes=2).to(device)
        models.meso4.eval()
        models.meso_inception = MesoInception4(num_classes=2).to(device)
        models.meso_inception.eval()
        models.xception = XceptionFingerprint(num_classes=2).to(device)
        models.xception.eval()
        logger.info("All models loaded successfully")
    except Exception as exc:
        logger.error(f"Model loading failed: {exc}")
    yield

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CyberThreatForge — Deepfake & Misinformation Detector",
    description="Multi-modal deepfake detection across video, audio, image, and text modalities.",
    version="1.0.0",
    lifespan=lifespan,
)

JOB_STORE: dict[str, dict[str, Any]] = {}
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _create_job() -> str:
    job_id = str(uuid.uuid4())
    JOB_STORE[job_id] = {
        "status": "accepted",
        "progress": 0,
        "result": None,
        "created_at": time.time(),
    }
    return job_id

def _record_custody(action: str, module: str, data: Optional[dict] = None) -> dict[str, Any]:
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from shared.chain_of_custody import ChainOfCustodyManager
    mgr = ChainOfCustodyManager()
    event = mgr.record(
        action=action,
        actor="deepfake_detector",
        module=module,
        data=data,
    )
    return {
        "timestamp": event.timestamp,
        "action": event.action,
        "actor": event.actor,
        "module": event.module,
        "hash": event.hash,
        "notes": event.notes,
    }

async def _progress_callback(job_id: str, percent: int, stage: str):
    if job_id in JOB_STORE:
        JOB_STORE[job_id]["progress"] = percent
        JOB_STORE[job_id]["stage"] = stage

# ---------------------------------------------------------------------------
# Ensemble fusion
# ---------------------------------------------------------------------------

def ensemble_fusion(modal_results: list[dict[str, Any]]) -> EnsembleFusionResult:
    """Weighted voting across modalities for final decision."""
    modality_weights = {
        "video": 0.35,
        "audio": 0.25,
        "image": 0.25,
        "text": 0.15,
    }

    total_score = 0.0
    total_weight = 0.0
    contributions: dict[str, float] = {}

    for res in modal_results:
        modality = res.get("modality", "unknown")
        score = res.get("ensemble_score", 0.5)
        weight = modality_weights.get(modality, 0.2)
        total_score += score * weight
        total_weight += weight
        contributions[modality] = score

    final_score = total_score / total_weight if total_weight > 0 else 0.5
    return EnsembleFusionResult(
        final_score=round(final_score, 4),
        is_deepfake=final_score > 0.5,
        modality_contributions=contributions,
    )

# ---------------------------------------------------------------------------
# Image analysis (standalone due to unique dependencies)
# ---------------------------------------------------------------------------

async def analyze_image_bytes(
    image_bytes: bytes, job_id: str,
) -> dict[str, Any]:
    """Analyze a single image for deepfake artifacts."""
    results: dict[str, Any] = {
        "modality": "image",
        "models_used": ["exif_metadata", "ela", "prnu", "gan_fingerprint"],
        "ensemble_score": 0.0,
        "is_deepfake": False,
    }

    try:
        from PIL import Image, ExifTags
        import io as _io

        img = Image.open(_io.BytesIO(image_bytes))
        results["image_size"] = f"{img.width}x{img.height}"
        results["format"] = img.format
        results["mode"] = img.mode

        exif_data = img.getexif()
        exif_dict: dict[str, Any] = {}
        for tag_id, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
            try:
                exif_dict[tag_name] = str(value)
            except Exception:
                exif_dict[tag_name] = str(value)
        results["exif"] = exif_dict
        results["has_exif"] = len(exif_dict) > 0

        img_rgb = img.convert("RGB")
        img_arr = np.array(img_rgb, dtype=np.float32)

        # ELA (Error Level Analysis)
        img.save(_io.BytesIO(), format="JPEG", quality=95)
        ela_score = 0.0
        try:
            resaved = Image.open(_io.BytesIO(img_arr.astype(np.uint8).tobytes()))
            ela_diff = np.abs(img_arr - np.array(resaved).astype(np.float32))
            ela_score = float(ela_diff.mean() / 255.0)
        except Exception:
            pass
        results["ela_score"] = min(1.0, ela_score * 10)

        # PRNU (Photo Response Non-Uniformity) noise estimation
        try:
            import cv2 as _cv2
            noise_pattern = img_arr - _cv2.GaussianBlur(img_arr, (5, 5), 0)
        except ImportError:
            from PIL import ImageFilter
            noise_pattern = img_arr - np.array(img_rgb.filter(ImageFilter.GaussianBlur(5)))
        noise_energy = float(np.std(noise_pattern))
        results["prnu_noise_energy"] = noise_energy
        results["prnu_anomalous"] = noise_energy < 1.0

        # GAN fingerprint matching via Xception model
        if models.xception is not None:
            try:
                import cv2 as _cv2
                resized = _cv2.resize(img_arr, (256, 256))
            except ImportError:
                resized = np.array(img_rgb.resize((256, 256), Image.LANCZOS))
            tensor = torch.from_numpy(resized).permute(2, 0, 1).float() / 255.0
            tensor = (tensor - 0.5) / 0.5
            tensor = tensor.unsqueeze(0).to(device)

            with torch.no_grad():
                logits, fingerprint = models.xception(tensor)
                prob = float(torch.softmax(logits, dim=1)[0, 1].cpu())
                results["gan_fingerprint_score"] = prob
            results["models_used"].append("xception_fingerprint")

        # Final image ensemble
        ela_w = 0.35
        prnu_w = 0.30
        gan_w = 0.35

        img_score = (
            ela_w * results.get("ela_score", 0.5) +
            prnu_w * (0.5 if results.get("prnu_anomalous") else 0.3) +
            gan_w * results.get("gan_fingerprint_score", 0.5)
        )
        results["ensemble_score"] = round(min(1.0, img_score), 4)
        results["is_deepfake"] = results["ensemble_score"] > 0.5

    except Exception as exc:
        logger.error(f"Image analysis failed: {exc}")
        results["error"] = str(exc)

    return results


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok" if any(models.status().values()) else "degraded",
        device=str(device),
        models_loaded=models.status(),
        cuda_available=torch.cuda.is_available(),
    )


@app.post("/analyze/video", response_model=AnalysisResponse)
async def analyze_video(
    file: UploadFile = File(...),
    audio_file: Optional[UploadFile] = File(None),
    job_id: Optional[str] = Form(None),
):
    job_id = job_id or _create_job()
    start = time.monotonic()
    custody_events: list[dict[str, Any]] = []

    custody_events.append(_record_custody("received", "video_pipeline", {"filename": file.filename}))
    JOB_STORE[job_id]["status"] = "processing"

    try:
        video_bytes = await file.read()
        audio_bytes = None
        if audio_file:
            audio_bytes = await audio_file.read()

        pipeline = VideoPipeline(
            device=device,
            meso_model=models.meso4,
            xception_model=models.xception,
        )

        def _progress(pct, stage):
            return _progress_callback(job_id, pct, stage)

        results = await pipeline.run(
            video_bytes, audio_bytes,
            progress_callback=_progress,
        )

        if models.meso_inception is not None:
            scores_meso_i = []
            try:
                import cv2 as _cv2
                cap = _cv2.VideoCapture(io.BytesIO(video_bytes))
                frame_count = 0
                while True:
                    ret, frame = cap.read()
                    if not ret or frame_count > 30:
                        break
                    if frame_count % 5 == 0:
                        rgb = _cv2.cvtColor(frame, _cv2.COLOR_BGR2RGB)
                        resized = _cv2.resize(rgb, (256, 256))
                        tensor = torch.from_numpy(resized).permute(2, 0, 1).float() / 255.0
                        tensor = (tensor - 0.5) / 0.5
                        with torch.no_grad():
                            out = models.meso_inception(tensor.unsqueeze(0).to(device))
                            scores_meso_i.append(float(torch.softmax(out, dim=1)[0, 1].cpu()))
                    frame_count += 1
                cap.release()
            except Exception:
                scores_meso_i = []
            if scores_meso_i:
                results["scores"]["meso_inception4"] = float(np.mean(scores_meso_i))
                results["models_used"].append("meso_inception4")

        fusion = ensemble_fusion([results])
        results["ensemble_fusion"] = fusion.model_dump()

        processing_time = (time.monotonic() - start) * 1000
        custody_events.append(_record_custody("analyzed", "video_pipeline", {
            "ensemble_score": results.get("ensemble_score"),
            "is_deepfake": results.get("is_deepfake"),
            "frames": results.get("frame_count"),
        }))

        JOB_STORE[job_id].update({"status": "completed", "result": results})

        return AnalysisResponse(
            job_id=job_id,
            status="completed",
            results=results,
            processing_time_ms=round(processing_time, 2),
            chain_of_custody=custody_events,
        )

    except Exception as exc:
        logger.exception("Video analysis failed")
        custody_events.append(_record_custody("error", "video_pipeline", {"error": str(exc)}))
        JOB_STORE[job_id]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AnalysisResponse(
                job_id=job_id,
                status="failed",
                results={"error": str(exc)},
                processing_time_ms=(time.monotonic() - start) * 1000,
                chain_of_custody=custody_events,
            ).model_dump(),
        )


@app.post("/analyze/audio", response_model=AnalysisResponse)
async def analyze_audio(
    file: UploadFile = File(...),
    reference_embedding: Optional[str] = Form(None),
):
    job_id = _create_job()
    start = time.monotonic()
    custody_events: list[dict[str, Any]] = []

    custody_events.append(_record_custody("received", "audio_pipeline", {"filename": file.filename}))
    JOB_STORE[job_id]["status"] = "processing"

    try:
        audio_bytes = await file.read()
        ref_emb: Optional[list[float]] = None
        if reference_embedding:
            try:
                ref_emb = json.loads(reference_embedding)
            except (json.JSONDecodeError, TypeError):
                pass

        pipeline = AudioPipeline(device=device, xception_model=models.xception)

        def _progress(pct, stage):
            return _progress_callback(job_id, pct, stage)

        results = await pipeline.run(
            audio_bytes, reference_embedding=ref_emb,
            progress_callback=_progress,
        )

        fusion = ensemble_fusion([results])
        results["ensemble_fusion"] = fusion.model_dump()

        processing_time = (time.monotonic() - start) * 1000
        custody_events.append(_record_custody("analyzed", "audio_pipeline", {
            "ensemble_score": results.get("ensemble_score"),
            "is_deepfake": results.get("is_deepfake"),
        }))

        JOB_STORE[job_id].update({"status": "completed", "result": results})

        return AnalysisResponse(
            job_id=job_id,
            status="completed",
            results=results,
            processing_time_ms=round(processing_time, 2),
            chain_of_custody=custody_events,
        )

    except Exception as exc:
        logger.exception("Audio analysis failed")
        custody_events.append(_record_custody("error", "audio_pipeline", {"error": str(exc)}))
        JOB_STORE[job_id]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AnalysisResponse(
                job_id=job_id,
                status="failed",
                results={"error": str(exc)},
                processing_time_ms=(time.monotonic() - start) * 1000,
                chain_of_custody=custody_events,
            ).model_dump(),
        )


@app.post("/analyze/image", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    job_id = _create_job()
    start = time.monotonic()
    custody_events: list[dict[str, Any]] = []

    custody_events.append(_record_custody("received", "image_pipeline", {"filename": file.filename}))
    JOB_STORE[job_id]["status"] = "processing"

    try:
        image_bytes = await file.read()

        def _progress(pct, stage):
            return _progress_callback(job_id, pct, stage)

        await _progress_callback(job_id, 10, "Reading image")
        results = await analyze_image_bytes(image_bytes, job_id)
        await _progress_callback(job_id, 90, "Fusing results")

        fusion = ensemble_fusion([results])
        results["ensemble_fusion"] = fusion.model_dump()

        processing_time = (time.monotonic() - start) * 1000
        custody_events.append(_record_custody("analyzed", "image_pipeline", {
            "ensemble_score": results.get("ensemble_score"),
            "is_deepfake": results.get("is_deepfake"),
        }))

        JOB_STORE[job_id].update({"status": "completed", "result": results})

        return AnalysisResponse(
            job_id=job_id,
            status="completed",
            results=results,
            processing_time_ms=round(processing_time, 2),
            chain_of_custody=custody_events,
        )

    except Exception as exc:
        logger.exception("Image analysis failed")
        custody_events.append(_record_custody("error", "image_pipeline", {"error": str(exc)}))
        JOB_STORE[job_id]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AnalysisResponse(
                job_id=job_id,
                status="failed",
                results={"error": str(exc)},
                processing_time_ms=(time.monotonic() - start) * 1000,
                chain_of_custody=custody_events,
            ).model_dump(),
        )


@app.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    job_id = request.job_id or _create_job()
    start = time.monotonic()
    custody_events: list[dict[str, Any]] = []

    custody_events.append(_record_custody("received", "text_pipeline", {
        "text_length": len(request.text),
    }))
    JOB_STORE[job_id]["status"] = "processing"

    try:
        pipeline = TextPipeline(device=device)

        def _progress(pct, stage):
            return _progress_callback(job_id, pct, stage)

        results = await pipeline.run(request.text, progress_callback=_progress)

        fusion = ensemble_fusion([results])
        results["ensemble_fusion"] = fusion.model_dump()

        processing_time = (time.monotonic() - start) * 1000
        custody_events.append(_record_custody("analyzed", "text_pipeline", {
            "ensemble_score": results.get("ensemble_score"),
            "is_deepfake": results.get("is_deepfake"),
        }))

        JOB_STORE[job_id].update({"status": "completed", "result": results})

        return AnalysisResponse(
            job_id=job_id,
            status="completed",
            results=results,
            processing_time_ms=round(processing_time, 2),
            chain_of_custody=custody_events,
        )

    except Exception as exc:
        logger.exception("Text analysis failed")
        custody_events.append(_record_custody("error", "text_pipeline", {"error": str(exc)}))
        JOB_STORE[job_id]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AnalysisResponse(
                job_id=job_id,
                status="failed",
                results={"error": str(exc)},
                processing_time_ms=(time.monotonic() - start) * 1000,
                chain_of_custody=custody_events,
            ).model_dump(),
        )


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    job = JOB_STORE.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "stage": job.get("stage", ""),
        "result": job.get("result"),
    }

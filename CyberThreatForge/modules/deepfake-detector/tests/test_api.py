"""Tests for the deepfake detector API, models, and ensemble fusion."""

import io
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

import numpy as np
import torch
from fastapi.testclient import TestClient

from api import app, ensemble_fusion, EnsembleFusionResult, models, device


client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_models():
    """Mock PyTorch models to avoid real model loading during tests."""
    with patch("api.models") as mock_models_module:
        mock_meso = MagicMock()
        mock_meso.eval.return_value = None
        mock_meso.to.return_value = mock_meso
        mock_meso.return_value = mock_meso

        mock_meso.forward = MagicMock(return_value=torch.tensor([[0.3, 0.7]]))

        mock_xception = MagicMock()
        mock_xception.eval.return_value = None
        mock_xception.to.return_value = mock_xception

        def xception_side_effect(x):
            return torch.tensor([[0.2, 0.8]]), torch.randn(1, 512)

        mock_xception.forward = MagicMock(side_effect=xception_side_effect)

        mock_models_module.meso4 = mock_meso
        mock_models_module.meso_inception = mock_meso
        mock_models_module.xception = mock_xception
        mock_models_module.status.return_value = {
            "meso4": True,
            "meso_inception": True,
            "xception_fingerprint": True,
        }

        mock_models_module.Meso4 = MagicMock(return_value=mock_meso)
        mock_models_module.MesoInception4 = MagicMock(return_value=mock_meso)
        mock_models_module.XceptionFingerprint = MagicMock(return_value=mock_xception)

        yield mock_models_module


@pytest.fixture
def sample_image_bytes():
    from PIL import Image
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_video_bytes():
    return b"\x00\x00\x00\x00" * 1000


@pytest.fixture
def sample_audio_bytes():
    sr = 16000
    t = np.linspace(0, 1, sr, endpoint=False)
    tone = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32).tobytes()
    return tone


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "device" in data
    assert "models_loaded" in data
    assert "cuda_available" in data


@patch("api.torch.cuda.is_available", return_value=True)
def test_health_cuda_available(mock_cuda):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["cuda_available"] is True


# ---------------------------------------------------------------------------
# Image analysis endpoint
# ---------------------------------------------------------------------------

def test_analyze_image_png(sample_image_bytes):
    response = client.post(
        "/analyze/image",
        files={"file": ("test.png", sample_image_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "results" in data
    assert "ensemble_score" in data["results"]
    assert "is_deepfake" in data["results"]
    assert "chain_of_custody" in data


def test_analyze_image_empty_returns_422():
    response = client.post("/analyze/image")
    assert response.status_code == 422


def test_analyze_image_jpeg():
    from PIL import Image
    img = Image.new("RGB", (50, 50), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    response = client.post(
        "/analyze/image",
        files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


# ---------------------------------------------------------------------------
# Video analysis endpoint
# ---------------------------------------------------------------------------

def test_analyze_video(sample_video_bytes):
    response = client.post(
        "/analyze/video",
        files={"file": ("test.mp4", sample_video_bytes, "video/mp4")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "results" in data
    assert "ensemble_score" in data["results"]
    assert "is_deepfake" in data["results"]
    assert "chain_of_custody" in data


def test_analyze_video_with_audio(sample_video_bytes, sample_audio_bytes):
    response = client.post(
        "/analyze/video",
        files={
            "file": ("test.mp4", sample_video_bytes, "video/mp4"),
            "audio_file": ("test.wav", sample_audio_bytes, "audio/wav"),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


# ---------------------------------------------------------------------------
# Audio analysis endpoint
# ---------------------------------------------------------------------------

def test_analyze_audio_wav(sample_audio_bytes):
    response = client.post(
        "/analyze/audio",
        files={"file": ("test.wav", sample_audio_bytes, "audio/wav")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "results" in data
    assert "spectrogram" in data["results"]
    assert "ensemble_score" in data["results"]


def test_analyze_audio_with_reference(sample_audio_bytes):
    ref_emb = json.dumps([0.1] * 52)
    response = client.post(
        "/analyze/audio",
        files={"file": ("test.wav", sample_audio_bytes, "audio/wav")},
        data={"reference_embedding": ref_emb},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


# ---------------------------------------------------------------------------
# Text analysis endpoint
# ---------------------------------------------------------------------------

def test_analyze_text():
    response = client.post(
        "/analyze/text",
        json={"text": "The quick brown fox jumps over the lazy dog."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "results" in data
    assert "perplexity" in data["results"]
    assert "burstiness" in data["results"]
    assert "watermark" in data["results"]
    assert "stylometry" in data["results"]
    assert "ensemble_score" in data["results"]


def test_analyze_text_long_content():
    long_text = " ".join(["word"] * 1000)
    response = client.post(
        "/analyze/text",
        json={"text": long_text},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


def test_analyze_text_empty_returns_422():
    response = client.post(
        "/analyze/text",
        json={"text": ""},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Job status endpoint
# ---------------------------------------------------------------------------

def test_get_job_status(sample_image_bytes):
    create_resp = client.post(
        "/analyze/image",
        files={"file": ("test.png", sample_image_bytes, "image/png")},
    )
    job_id = create_resp.json()["job_id"]

    resp = client.get(f"/job/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["job_id"] == job_id


def test_get_job_status_not_found():
    resp = client.get("/job/nonexistent-uuid")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Ensemble fusion
# ---------------------------------------------------------------------------

def test_ensemble_fusion_single_modality():
    results = [{"modality": "video", "ensemble_score": 0.8}]
    fusion = ensemble_fusion(results)
    assert isinstance(fusion, EnsembleFusionResult)
    assert fusion.final_score > 0.5
    assert fusion.is_deepfake is True


def test_ensemble_fusion_mixed():
    results = [
        {"modality": "video", "ensemble_score": 0.9},
        {"modality": "audio", "ensemble_score": 0.3},
    ]
    fusion = ensemble_fusion(results)
    assert 0.3 < fusion.final_score < 0.9
    assert "video" in fusion.modality_contributions
    assert "audio" in fusion.modality_contributions


def test_ensemble_fusion_low_scores():
    results = [
        {"modality": "video", "ensemble_score": 0.2},
        {"modality": "text", "ensemble_score": 0.1},
    ]
    fusion = ensemble_fusion(results)
    assert fusion.is_deepfake is False
    assert fusion.final_score < 0.5


def test_ensemble_fusion_empty():
    fusion = ensemble_fusion([])
    assert fusion.final_score == 0.5
    assert fusion.is_deepfake is False


# ---------------------------------------------------------------------------
# Model definitions (unit tests)
# ---------------------------------------------------------------------------

def test_meso4_forward():
    from models.mesonet import Meso4
    model = Meso4(num_classes=2)
    model.eval()
    x = torch.randn(1, 3, 256, 256)
    with torch.no_grad():
        out = model(x)
    assert out.shape == (1, 2)


def test_meso_inception4_forward():
    from models.mesonet import MesoInception4
    model = MesoInception4(num_classes=2)
    model.eval()
    x = torch.randn(1, 3, 256, 256)
    with torch.no_grad():
        out = model(x)
    assert out.shape == (1, 2)


def test_xception_fingerprint_forward():
    from models.xception_fingerprint import XceptionFingerprint
    model = XceptionFingerprint(num_classes=2)
    model.eval()
    x = torch.randn(1, 3, 256, 256)
    with torch.no_grad():
        logits, fingerprint = model(x)
    assert logits.shape == (1, 2)
    assert fingerprint.shape == (1, 512)


def test_xception_extract_fingerprint():
    from models.xception_fingerprint import XceptionFingerprint
    model = XceptionFingerprint(num_classes=2)
    model.eval()
    x = torch.randn(1, 3, 256, 256)
    with torch.no_grad():
        fp = model.extract_fingerprint(x)
    assert fp.shape == (1, 512)


# ---------------------------------------------------------------------------
# Pipeline unit tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_text_pipeline_run():
    from pipelines.text_pipeline import TextPipeline
    pipeline = TextPipeline(device=torch.device("cpu"))
    result = await pipeline.run("This is a test sentence.")
    assert result["modality"] == "text"
    assert "ensemble_score" in result
    assert "is_deepfake" in result
    assert result["is_deepfake"] in (True, False)


@pytest.mark.asyncio
async def test_text_pipeline_empty_input():
    from pipelines.text_pipeline import TextPipeline
    pipeline = TextPipeline(device=torch.device("cpu"))
    result = await pipeline.run("   ")
    assert "error" in result


def test_text_burstiness():
    from pipelines.text_pipeline import TextPipeline
    pipeline = TextPipeline(device=torch.device("cpu"))
    result = pipeline.burstiness_analysis("hello world hello world hello")
    assert "burstiness_score" in result
    assert "distribution" in result


def test_stylometric_analysis():
    from pipelines.text_pipeline import TextPipeline
    pipeline = TextPipeline(device=torch.device("cpu"))
    result = pipeline.stylometric_analysis("This is a test. It has two sentences. The end.")
    assert "sentence_count" in result
    assert result["sentence_count"] == 3


# ---------------------------------------------------------------------------
# Chain of custody integration
# ---------------------------------------------------------------------------

def test_chain_of_custody_in_response(sample_image_bytes):
    resp = client.post(
        "/analyze/image",
        files={"file": ("test.png", sample_image_bytes, "image/png")},
    )
    data = resp.json()
    assert len(data["chain_of_custody"]) >= 2
    assert data["chain_of_custody"][0]["action"] == "received"
    assert data["chain_of_custody"][1]["action"] == "analyzed"
    for event in data["chain_of_custody"]:
        assert "timestamp" in event
        assert "hash" in event
        assert "module" in event

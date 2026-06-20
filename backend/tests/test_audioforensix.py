import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_audioforensix.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_audioforensix_flow():
    # 1. Ingest Audio
    response = client.post(
        "/api/audioforensix/ingest",
        json={
            "sample_id": "AUDIO-101",
            "filename": "intercepted_call.wav",
            "duration_seconds": 45.5,
            "format": "WAV"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "INGESTED"

    # 2. Detect Deepfake
    response = client.post(
        "/api/audioforensix/detect-deepfake",
        json={
            "sample_id": "AUDIO-101",
            "claimed_identity": "CEO_Target"
        }
    )
    assert response.status_code == 200
    assert "match_confidence" in response.json()
    assert "is_deepfake" in response.json()

    # 3. Reconstruct Environment
    response = client.post(
        "/api/audioforensix/reconstruct-environment",
        json={
            "sample_id": "AUDIO-101"
        }
    )
    assert response.status_code == 200
    assert "rt60_decay" in response.json()
    assert "estimated_environment" in response.json()

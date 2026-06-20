import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_droneguard.db"
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

def test_droneguard_flow():
    # 1. Telemetry Spoofing
    response = client.post(
        "/api/droneguard/analyze-telemetry",
        json={
            "drone_id": "UAV-ALPHA-99",
            "gps_lat": 40.7128,
            "gps_lon": -74.0060,
            "ins_lat": 40.7135, # Forced variance
            "ins_lon": -74.0065
        }
    )
    assert response.status_code == 200
    assert response.json()["is_spoofed"] is True
    assert "GPS_SPOOFING_DETECTED" in response.json()["action_taken"]

    # 2. Malware Analysis
    response = client.post(
        "/api/droneguard/analyze-malware",
        json={
            "firmware_hash": "A1B2C3D4_ROGUE_FIRMWARE"
        }
    )
    assert response.status_code == 200
    assert response.json()["payload_extracted"] is True

    # 3. Swarm Simulation
    response = client.post(
        "/api/droneguard/simulate-swarm",
        json={
            "swarm_id": "SWARM-ZETA",
            "drone_count": 500,
            "formation_type": "HUNTER_KILLER"
        }
    )
    assert response.status_code == 200
    assert response.json()["saturation_level"] == 750.0
    assert "CRITICAL_SATURATION" in response.json()["threat_assessment"]

    # 4. Compliance Evidence
    response = client.post(
        "/api/droneguard/secure-evidence",
        json={
            "case_id": "CASE-2026-X1",
            "file_name": "intercept_vid_01.mp4",
            "raw_data": "binary_video_data_stream..."
        }
    )
    assert response.status_code == 200
    assert response.json()["is_compliant"] is True
    assert len(response.json()["sha256_hash"]) == 64

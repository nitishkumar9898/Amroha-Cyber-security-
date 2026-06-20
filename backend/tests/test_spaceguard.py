import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_spaceguard.db"
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

def test_spaceguard_flow():
    # 1. Analyze Satellite Telemetry
    response = client.post(
        "/api/spaceguard/analyze-sat-comm",
        json={
            "satellite_id": "ORBIT-X1",
            "protocol": "CCSDS",
            "signal_to_noise_ratio": 4.5,
            "auth_handshake_valid": False # Hijacking indicator
        }
    )
    assert response.status_code == 200
    assert response.json()["is_hijacked"] is True
    assert "Hijacking Detected" in response.json()["status_message"]

    # 2. Simulate Orbital Attack
    response = client.post(
        "/api/spaceguard/simulate-orbital-attack",
        json={
            "mission_name": "Project Artemis Defense",
            "payload_type": "Comms Array",
            "firmware_hash": "HASH_COMPROMISED_PAYLOAD"
        }
    )
    assert response.status_code == 200
    assert response.json()["vulnerability_found"] is True
    assert response.json()["orbital_risk_score"] > 9.0

    # 3. Protect Asset
    response = client.post(
        "/api/spaceguard/protect-asset",
        json={
            "asset_id": "ORBIT-X1",
            "threat_intel_level": "CRITICAL"
        }
    )
    assert response.status_code == 200
    assert "Kessler Syndrome" in response.json()["defensive_posture"]

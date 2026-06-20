import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_metaguard.db"
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

def test_metaguard_flow():
    # 1. Asset Tracking (Laundering)
    response = client.post(
        "/api/metaguard/track-asset",
        json={
            "asset_id": "NFT-LAND-1337",
            "wallet_hops": 6,
            "time_window_seconds": 45.0
        }
    )
    assert response.status_code == 200
    assert response.json()["is_laundering_risk"] is True
    assert "VIRTUAL_LAUNDERING_DETECTED" in response.json()["action_taken"]

    # 2. Avatar Behavior (Social Engineering)
    response = client.post(
        "/api/metaguard/analyze-avatar",
        json={
            "avatar_id": "USER-X99",
            "kinematic_jitter": 9.5,
            "manipulative_language": True
        }
    )
    assert response.status_code == 200
    assert response.json()["social_engineering_risk"] is True
    assert "SOCIAL_ENGINEERING_RISK" in response.json()["risk_assessment"]

    # 3. Crime Correlation
    response = client.post(
        "/api/metaguard/correlate-crime",
        json={
            "virtual_incident_id": "HEIST-001",
            "virtual_ip_log": "192.168.1.1 (TOR NODE)"
        }
    )
    assert response.status_code == 200
    assert "HW-" in response.json()["hardware_id_hash"]
    assert "Obfuscated" in response.json()["physical_location_estimate"]

    # 4. Evidence Visualization
    response = client.post(
        "/api/metaguard/visualize-evidence",
        json={
            "scene_id": "SCENE-XYZ",
            "raw_spatial_data": "{...point cloud...}"
        }
    )
    assert response.status_code == 200
    assert response.json()["is_training_ready"] is True
    assert "manifest.json" in response.json()["manifest_url"]

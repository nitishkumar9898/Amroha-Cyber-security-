import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_neuroguard.db"
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

def test_neuroguard_flow():
    # 1. Analyze Benign Telemetry
    response = client.post(
        "/api/neuroguard/analyze-telemetry",
        json={
            "subject_id": "OP-774",
            "alpha_band_hz": 10.5,
            "beta_band_hz": 20.0,
            "gamma_band_hz": 40.0
        }
    )
    assert response.status_code == 200
    assert response.json()["is_anomalous"] is False
    assert "BENIGN" in response.json()["status_message"]

    # 2. Analyze Anomalous Telemetry
    response = client.post(
        "/api/neuroguard/analyze-telemetry",
        json={
            "subject_id": "OP-991",
            "alpha_band_hz": 12.0,
            "beta_band_hz": 25.0,
            "gamma_band_hz": 95.0 # High Gamma = Synthetic Stimulation
        }
    )
    assert response.status_code == 200
    assert response.json()["is_anomalous"] is True
    assert response.json()["anomaly_type"] == "SYNTHETIC_STIMULATION"

    # 3. Simulate BCI Hack
    response = client.post(
        "/api/neuroguard/simulate-bci-hack",
        json={
            "attack_vector": "MEMORY_ALTERATION"
        }
    )
    assert response.status_code == 200
    assert "hippocampus" in response.json()["biological_impact"].lower()
    
    # 4. Enforce Privacy
    response = client.post(
        "/api/neuroguard/enforce-privacy",
        json={
            "data_packet_id": "PKT-112233",
            "raw_thought_data": "0xABC123_NEURAL_STREAM_DATA"
        }
    )
    assert response.status_code == 200
    assert response.json()["is_secure"] is True
    assert response.json()["encryption_standard"] == "HOMOMORPHIC"

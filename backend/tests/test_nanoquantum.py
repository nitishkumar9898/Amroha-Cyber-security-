import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_nanoquantum.db"
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

def test_nanoquantum_flow():
    # 1. Analyze Sensor
    response = client.post(
        "/api/nanoquantum/analyze-sensor",
        json={
            "device_id": "NQ-SENSOR-001",
            "electron_spin_variance": 6.5,
            "entanglement_stable": False
        }
    )
    assert response.status_code == 200
    assert response.json()["is_hijacked"] is True
    assert "CRITICAL" in response.json()["status_message"]

    # 2. Simulate Threat
    response = client.post(
        "/api/nanoquantum/simulate-nano-threat",
        json={
            "threat_type": "GREY_GOO",
            "time_elapsed_seconds": 60
        }
    )
    assert response.status_code == 200
    assert response.json()["replication_rate"] == 1.05
    assert response.json()["material_consumed_kg"] > 0.01

    # 3. Validate Hardware
    response = client.post(
        "/api/nanoquantum/validate-hardware",
        json={
            "hardware_id": "HW-NQ-009",
            "pqc_algorithm_applied": "KYBER_1024"
        }
    )
    assert response.status_code == 200
    assert response.json()["atomic_integrity_verified"] is True

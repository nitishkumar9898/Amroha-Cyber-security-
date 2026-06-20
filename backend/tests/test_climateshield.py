import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_climateshield.db"
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

def test_climateshield_flow():
    # 1. Simulate Infra Attack
    response = client.post(
        "/api/climateshield/simulate-infra-attack",
        json={
            "infrastructure_type": "WATER",
            "weather_event": "DROUGHT",
            "cyber_attack_vector": "SCADA_HIJACK"
        }
    )
    assert response.status_code == 200
    assert response.json()["cascading_impact_score"] > 9.0
    assert "Desalination" in response.json()["analysis_details"]

    # 2. Simulate Climate Manipulation
    response = client.post(
        "/api/climateshield/simulate-climate-manipulation",
        json={
            "manipulation_vector": "CLOUD_SEEDING_HIJACK",
            "projected_years": 50
        }
    )
    assert response.status_code == 200
    assert response.json()["economic_impact_trillions"] == 15.0 # 50 * 0.3
    assert response.json()["ecological_damage_index"] == 5.0 # 50 * 0.1

    # 3. Generate Resilience Plan
    response = client.post(
        "/api/climateshield/generate-resilience-plan",
        json={
            "scenario_trigger": "WATER_INFRASTRUCTURE_COLLAPSE",
            "severity_score": 9.5
        }
    )
    assert response.status_code == 200
    assert "hydro-rationing" in response.json()["recovery_strategy"]
    assert response.json()["estimated_recovery_days"] == 45

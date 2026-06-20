import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_gridshield.db"
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

def test_gridshield_flow():
    # 1. SCADA Analysis
    response = client.post(
        "/api/gridshield/analyze-scada",
        json={
            "device_id": "PLC-99",
            "protocol": "Modbus",
            "packet_payload": "UNAUTH_WRITE_REG_4001",
            "frequency_hz": 150.0
        }
    )
    assert response.status_code == 200
    assert response.json()["is_anomalous"] is True
    assert "high-frequency" in response.json()["flag_reason"]

    # 2. Cyber-Physical Simulation (Turbine Overspeed)
    response = client.post(
        "/api/gridshield/simulate-physical",
        json={
            "target_component": "Turbine-A",
            "injected_rpm": 4500.0,
            "normal_operating_rpm": 3000.0
        }
    )
    assert response.status_code == 200
    assert response.json()["kinetic_damage_probability"] > 50.0
    assert "CRITICAL" in response.json()["structural_integrity_warning"]

    # 3. Resilience Planning
    response = client.post(
        "/api/gridshield/plan-resilience",
        json={
            "grid_sector": "Sector-7G",
            "current_load_mw": 500.0,
            "compromised_nodes": 8
        }
    )
    assert response.status_code == 200
    assert response.json()["islanding_required"] is True
    assert response.json()["load_shedding_percentage"] == 35.0

    # 4. Threat Forecasting
    response = client.post(
        "/api/gridshield/forecast-threat",
        json={
            "region": "US-EAST",
            "iot_integration_level": 8.5,
            "past_incidents_count": 5
        }
    )
    assert response.status_code == 200
    assert response.json()["five_year_risk_score"] > 50.0
    assert "IoT" in response.json()["primary_threat_vector"]

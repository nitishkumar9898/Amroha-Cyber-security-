import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_omnisimulator.db"
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

def test_omnisimulator_flow():
    # 1. Launch Scenario
    response = client.post(
        "/api/omnisimulator/launch-scenario",
        json={
            "scenario_id": "SCENARIO-QGRID",
            "name": "Operation Midnight: Quantum Grid Collapse",
            "description": "A devastating cyber warfare simulation."
        }
    )
    assert response.status_code == 200
    assert response.json()["global_resilience_score"] == 100.0

    # 2. Trigger Event
    response = client.post(
        "/api/omnisimulator/trigger-event",
        json={
            "scenario_id": "SCENARIO-QGRID",
            "source_module": "SpaceGuard",
            "event_description": "Satellite Command & Control link hijacked.",
            "severity": "CRITICAL"
        }
    )
    assert response.status_code == 200
    
    # Check that cascades were triggered
    # (Since it's random, we can't assert an exact number easily, but it should be calculated)
    assert "cascades_triggered" in response.json()
    assert response.json()["new_resilience_score"] <= 100.0

    # 3. Get Global State
    response = client.get("/api/omnisimulator/global-state/SCENARIO-QGRID")
    assert response.status_code == 200
    assert response.json()["total_events"] == 1
    assert "total_cascades" in response.json()

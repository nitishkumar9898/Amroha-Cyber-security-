import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.redteam import RedTeamScenario

# Setup an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_redteam.db"
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

def test_redteam_flow():
    # 1. Generate scenario
    response = client.post(
        "/api/redteam/scenarios/generate",
        json={"name": "Test Scenario", "description": "Test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Scenario"
    scenario_id = data["id"]
    
    # 2. Start simulation
    response = client.post(
        "/api/redteam/simulation/start",
        json={"scenario_id": scenario_id}
    )
    assert response.status_code == 200
    data = response.json()
    run_id = data["id"]
    assert data["status"] == "IN_PROGRESS"
    
    # 3. Submit actions
    response = client.post(
        f"/api/redteam/simulation/{run_id}/action",
        json={"team": "blue", "action_type": "isolate", "target": "node-A"}
    )
    assert response.status_code == 200
    
    # Loop to finish the simulation for analysis
    for _ in range(5):
        client.post(f"/api/redteam/simulation/{run_id}/action", json={"team": "blue", "action_type": "defend", "target": "all"})
        client.post(f"/api/redteam/simulation/{run_id}/action", json={"team": "red", "action_type": "attack", "target": "all"})
        
    # 4. Get Analysis
    response = client.get(f"/api/redteam/simulation/{run_id}/analysis")
    assert response.status_code == 200
    report = response.json()
    assert report["run_id"] == run_id
    assert report["status"] == "COMPLETED"
    assert "recommendations" in report

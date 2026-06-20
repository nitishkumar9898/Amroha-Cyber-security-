import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_swarmforge.db"
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

def test_swarmforge_flow():
    # 1. Initialize Attack
    response = client.post(
        "/api/swarmforge/simulate-attack",
        json={
            "target_infrastructure": "Edge-Gateway-Cluster",
            "swarm_size": 5000,
            "attack_vector": "LATERAL_MOVEMENT"
        }
    )
    assert response.status_code == 200
    sim_id = response.json()["simulation_id"]
    assert response.json()["status"] == "SWARM_DEPLOYED"
    
    # 2. Analyze Behavior
    response = client.get(f"/api/swarmforge/analyze-behavior/{sim_id}")
    assert response.status_code == 200
    assert "coordination_score" in response.json()
    assert "Secondary-Backup" in response.json()["predicted_pivot_target"] or "Adjacent-Subnet" in response.json()["predicted_pivot_target"]
    
    # 3. Deploy Counter Swarm
    response = client.post(
        "/api/swarmforge/deploy-counter-swarm",
        json={
            "simulation_id": sim_id,
            "strategy_used": "HONEYPOT_DECOY"
        }
    )
    assert response.status_code == 200
    assert response.json()["neutralization_percentage"] > 0
    # Depending on random seed, it might or might not deactivate, but the call should succeed.

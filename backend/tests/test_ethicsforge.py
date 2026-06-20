import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ethicsforge.db"
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

def test_ethicsforge_flow():
    # 1. Create a Policy
    response = client.post(
        "/api/ethicsforge/policies",
        json={
            "policy_name": "HITL Requirement for Isolation",
            "description": "All AUTOMATED_ISOLATION actions require Human-in-the-loop review.",
            "severity_level": "CRITICAL"
        }
    )
    assert response.status_code == 200
    
    # 2. Evaluate Action (VETO expected)
    response = client.post(
        "/api/ethicsforge/evaluate-action",
        json={
            "module_source": "ResponseForge",
            "proposed_action": "AUTOMATED_ISOLATION of Subnet A",
            "action_context": "DDoS detected, isolating immediately."
        }
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "VETOED"
    
    # 3. Evaluate Action (APPROVED expected)
    response = client.post(
        "/api/ethicsforge/evaluate-action",
        json={
            "module_source": "NetGuard",
            "proposed_action": "LOG_TRAFFIC_ANOMALY",
            "action_context": "Found 10GB exfiltration"
        }
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "APPROVED"
    
    # 4. Scan Bias
    response = client.post(
        "/api/ethicsforge/scan-bias",
        json={
            "model_name": "InsiderRisk_v2",
            "dataset_signature": "DATA_WITH_DEMO_SKEW"
        }
    )
    assert response.status_code == 200
    assert response.json()["demographic_skew_detected"] is True
    
    # 5. Fetch Transparency Report
    # We generated an audit log in step 2. It should have ID 1.
    response = client.get("/api/ethicsforge/transparency-report/1")
    assert response.status_code == 200
    assert "VETOED" in response.json()["xai_explanation"]

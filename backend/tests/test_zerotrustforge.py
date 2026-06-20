import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_zerotrustforge.db"
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

def test_zerotrustforge_flow():
    # 1. Continuous Authentication
    response = client.post(
        "/api/zerotrustforge/authenticate",
        json={
            "user_id": "USER-999",
            "device_id": "DEV-XYZ",
            "ip_address": "192.168.1.100",
            "is_off_hours": True,
            "geo_location_anomaly": True
        }
    )
    assert response.status_code == 200
    assert response.json()["context_anomalies"] == 2
    assert response.json()["trust_score"] < 50.0
    assert response.json()["auth_status"] == "Untrusted"

    # 2. Micro-Segmentation (Default Deny)
    response = client.post(
        "/api/zerotrustforge/create-segment",
        json={
            "source_segment": "HR_VLAN",
            "target_segment": "FINANCE_DB",
            "is_whitelisted": False
        }
    )
    assert response.status_code == 200
    assert "BLOCKED" in response.json()["status"]

    # 3. Least Privilege Access
    response = client.post(
        "/api/zerotrustforge/evaluate-access",
        json={
            "user_id": "USER-999",
            "resource_id": "SERVER-1",
            "user_trust_score": 45.0,
            "required_trust_score": 80.0
        }
    )
    assert response.status_code == 200
    assert response.json()["access_granted"] is False
    assert "Access Denied" in response.json()["reason"]

    # 4. Policy Enforcement
    response = client.post(
        "/api/zerotrustforge/enforce-policy",
        json={
            "trigger_event": "MULTIPLE_FAILED_LOGINS",
            "target_user": "USER-999",
            "trust_score": 45.0
        }
    )
    assert response.status_code == 200
    assert "Terminate Session" in response.json()["action_taken"]

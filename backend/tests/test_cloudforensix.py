import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Setup an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cloudforensix.db"
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

def test_cloudforensix_flow():
    # 1. Report Incident
    response = client.post(
        "/api/cloudforensix/incidents",
        json={"provider": "AWS", "severity": "HIGH"}
    )
    assert response.status_code == 200
    incident_id = response.json()["id"]

    # 2. Analyze Logs
    response = client.post(
        "/api/cloudforensix/analyze-logs",
        json={
            "incident_id": incident_id,
            "log_source": "CloudTrail",
            "raw_logs": [
                {"eventName": "S3Transfer", "sourceRegion": "eu-central-1", "destRegion": "us-east-1"},
                {"eventName": "DeleteTrail", "region": "us-east-1"}
            ]
        }
    )
    assert response.status_code == 200
    assert response.json()["anomalies_detected"] == 1

    # 3. Scan Container
    response = client.post(
        "/api/cloudforensix/scan-container",
        json={
            "incident_id": incident_id,
            "image_hash": "sha256:bad_image_123",
            "namespace": "kube-system"
        }
    )
    assert response.status_code == 200
    assert response.json()["escape_detected"] is True

    # 4. Trace Serverless
    response = client.post(
        "/api/cloudforensix/trace-serverless",
        json={
            "incident_id": incident_id,
            "function_name": "crypto_miner_lambda"
        }
    )
    assert response.status_code == 200
    assert response.json()["malicious_payload_detected"] is True

    # 5. Check Residency
    response = client.get(f"/api/cloudforensix/residency-compliance/{incident_id}")
    assert response.status_code == 200
    assert response.json()["is_compliant"] is False
    assert len(response.json()["violations"]) == 1

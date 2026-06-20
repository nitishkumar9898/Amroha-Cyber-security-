import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_humanforge.db"
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

def test_humanforge_flow():
    # 1. Phishing Detection
    response = client.post(
        "/api/humanforge/detect-phishing",
        json={
            "message_id": "MSG-001",
            "content_body": "Urgent action required: Reset your password immediately via this wire transfer link.",
            "sender_domain": "admin-support.co"
        }
    )
    assert response.status_code == 200
    assert response.json()["is_phishing"] is True
    assert response.json()["confidence_score"] == 100.0

    # 2. Psychological Manipulation
    response = client.post(
        "/api/humanforge/analyze-manipulation",
        json={
            "transcript_id": "TRANS-XYZ",
            "urgency_level": 9.5,
            "authority_impersonation": True
        }
    )
    assert response.status_code == 200
    assert "COGNITIVE_EXPLOITATION" in response.json()["manipulation_type"]
    assert response.json()["severity_level"] == "CRITICAL"

    # 3. Awareness Simulation
    response = client.post(
        "/api/humanforge/simulate-awareness",
        json={
            "employee_id": "EMP-505",
            "target_vulnerability": "FINANCIAL_URGENCY"
        }
    )
    assert response.status_code == 200
    assert "payroll" in response.json()["payload_content"].lower()
    assert response.json()["difficulty_rating"] == 8.5

    # 4. Insider Threat Link
    response = client.post(
        "/api/humanforge/link-insider",
        json={
            "employee_id": "EMP-505",
            "base_insider_risk": 50.0,
            "failed_simulations_count": 3
        }
    )
    assert response.status_code == 200
    assert response.json()["adjusted_insider_risk"] > 50.0
    assert "1.45" in response.json()["reasoning"]

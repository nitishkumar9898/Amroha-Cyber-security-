import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_innovateguard.db"
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

def test_innovateguard_flow():
    # 1. Detect Idea
    response = client.post(
        "/api/innovateguard/detect-idea",
        json={
            "research_data_id": "RES-2026-001",
            "research_text": "We have developed a novel algorithm for a quantum-resistant sub-molecular sensor."
        }
    )
    assert response.status_code == 200
    assert response.json()["novelty_score"] > 90.0
    assert "novel sensory architecture" in response.json()["generated_claim"]

    # 2. Investigate Theft
    response = client.post(
        "/api/innovateguard/investigate-theft",
        json={
            "user_id": "DEV-088",
            "data_volume_gb": 12.5,
            "time_of_access": "NON_BUSINESS"
        }
    )
    assert response.status_code == 200
    assert response.json()["is_exfiltration_risk"] is True
    assert "IP_EXFILTRATION_RISK" in response.json()["action_taken"]

    # 3. Track Innovation
    response = client.post(
        "/api/innovateguard/track-innovation",
        json={
            "project_name": "Project Apollo",
            "owner_id": "RESEARCH-LEAD",
            "current_stage": "PATENT_PENDING"
        }
    )
    assert response.status_code == 200
    assert response.json()["current_stage"] == "PATENT_PENDING"

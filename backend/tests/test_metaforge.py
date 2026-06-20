import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_metaforge.db"
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

def test_metaforge_flow():
    # 1. Ingest Metric
    response = client.post(
        "/api/metaforge/ingest-metric",
        json={
            "source_module": "SpaceGuard",
            "latency_ms": 650.0,
            "error_rate": 0.01
        }
    )
    assert response.status_code == 200
    assert "edge-caching" in response.json()["optimization_suggestion"]

    # 2. Manage Evolution
    response = client.post(
        "/api/metaforge/manage-evolution",
        json={
            "target_module": "NetGuard",
            "current_version": "1.2.4"
        }
    )
    assert response.status_code == 200
    assert response.json()["proposed_version"] == "1.3.0"

    # 3. Detect Anomaly
    response = client.post(
        "/api/metaforge/detect-anomaly",
        json={
            "subsystem": "SwarmForge AI",
            "anomaly_type": "BYPASS_ATTEMPT"
        }
    )
    assert response.status_code == 200
    assert response.json()["severity"] == "CRITICAL"
    assert "INTERNAL_BREACH" in response.json()["action_taken"]

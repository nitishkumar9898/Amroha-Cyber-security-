import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_resilientforge.db"
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

def test_resilientforge_flow():
    # 1. Simulate Disaster
    response = client.post(
        "/api/resilientforge/simulate-disaster",
        json={
            "scenario_name": "RANSOMWARE",
            "target_infrastructure": "Core-DB-Cluster",
            "simulated_downtime_hours": 24.0
        }
    )
    assert response.status_code == 200
    assert response.json()["optimized_rto_hours"] == 6.0
    
    # 2. Verify Clean Backup
    response = client.post(
        "/api/resilientforge/verify-backup",
        json={
            "backup_id": "BKP-2026-06-20",
            "file_signature": "CLEAN_HASH_XYZ"
        }
    )
    assert response.status_code == 200
    assert response.json()["is_corrupt"] is False
    assert response.json()["malware_detected"] is False
    
    # 3. Verify Corrupted Backup
    response = client.post(
        "/api/resilientforge/verify-backup",
        json={
            "backup_id": "BKP-2026-06-19",
            "file_signature": "HASH_CORRUPT_MALWARE_EMBEDDED"
        }
    )
    assert response.status_code == 200
    assert response.json()["is_corrupt"] is True
    assert response.json()["malware_detected"] is True
    
    # 4. Trigger Auto Heal
    response = client.post(
        "/api/resilientforge/trigger-heal",
        json={
            "asset_id": "Core-DB-Cluster-01",
            "initial_state": "CORRUPTED"
        }
    )
    assert response.status_code == 200
    assert response.json()["final_state"] == "HEALED"
    assert response.json()["reconstruction_method"] == "AI_REBUILD_FROM_FRAGMENTS"

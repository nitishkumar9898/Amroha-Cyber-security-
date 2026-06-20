import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_globaljurix.db"
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

def test_globaljurix_flow():
    # 1. Jurisdiction Mapping
    response = client.post(
        "/api/globaljurix/map-jurisdiction",
        json={
            "case_id": "CASE-101",
            "source_country": "Russia",
            "target_country": "Germany"
        }
    )
    assert response.status_code == 200
    assert response.json()["jurisdiction_conflict"] is True
    assert "GDPR" in response.json()["primary_legal_framework"]

    # 2. Evidence Packaging
    response = client.post(
        "/api/globaljurix/package-evidence",
        json={
            "evidence_id": "EVID-55",
            "raw_data_string": "PCAP_DATA_12345"
        }
    )
    assert response.status_code == 200
    assert response.json()["is_compliant"] is True
    assert len(response.json()["file_hash"]) == 64 # SHA-256 length

    # 3. MLAT Checking
    response = client.post(
        "/api/globaljurix/check-mlat",
        json={
            "requesting_country": "USA",
            "receiving_country": "UK"
        }
    )
    assert response.status_code == 200
    assert response.json()["expedited_routing_available"] is True
    assert response.json()["estimated_processing_days"] == 7

    # 4. Cross Module Link
    response = client.post(
        "/api/globaljurix/link-collabguard",
        json={
            "case_id": "CASE-101",
            "agency_code": "INTERPOL"
        }
    )
    assert response.status_code == 200
    assert "CollabGuard" in response.json()["status"]

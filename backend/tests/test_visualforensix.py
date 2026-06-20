import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_visualforensix.db"
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

def test_visualforensix_flow():
    # 1. Ingest
    response = client.post(
        "/api/visualforensix/ingest",
        json={
            "asset_id": "IMG-001",
            "filename": "evidence1.jpg",
            "media_type": "image",
            "file_size_kb": 2048.5
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "INGESTED"

    # 2. Analyze
    response = client.post(
        "/api/visualforensix/analyze",
        json={
            "asset_id": "IMG-001",
            "media_type": "image"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pixel_analysis"] is not None
    assert "ela_score" in data["pixel_analysis"]

    # 3. Generate Report
    response = client.post(
        "/api/visualforensix/generate-report",
        json={
            "asset_id": "IMG-001",
            "pixel_analysis": data["pixel_analysis"]
        }
    )
    assert response.status_code == 200
    report_data = response.json()
    assert "report_hash" in report_data
    assert "admissibility_score" in report_data
    assert report_data["report_data"]["forensic_conclusion"] in ["TAMPERED", "AUTHENTIC"]

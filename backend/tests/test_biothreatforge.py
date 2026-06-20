import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_biothreatforge.db"
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

def test_biothreatforge_analyze_sequence():
    response = client.post(
        "/api/biothreatforge/analyze-sequence",
        json={
            "sequence_id": "SEQ-9092",
            "sequence_hash": "a1b2c3d4e5f6",
            "source_facility": "Alpha Genomics Lab"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "bioweapon_probability" in data
    assert "pathogenic_markers_found" in data

def test_biothreatforge_monitor_facility():
    response = client.post(
        "/api/biothreatforge/monitor-facility",
        json={
            "facility_id": "FACILITY-X"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "scada_anomaly_score" in data
    assert "unauthorized_prints_detected" in data

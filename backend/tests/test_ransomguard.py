import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Setup an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ransomguard.db"
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

def test_ransomguard_flow():
    # 1. Report Incident
    response = client.post(
        "/api/ransomguard/incidents",
        json={
            "target_entity": "Acme Corp",
            "ransom_note": "Your files are encrypted by Ryuk. Send 5 BTC.",
            "demanded_amount": 5.0,
            "currency": "BTC"
        }
    )
    assert response.status_code == 200
    incident = response.json()
    incident_id = incident["id"]
    assert incident["status"] == "OPEN"
    
    # 2. Trace Crypto Funds
    response = client.post(
        "/api/ransomguard/trace",
        json={
            "incident_id": incident_id,
            "initial_wallet_address": "bc1q_initial_test"
        }
    )
    assert response.status_code == 200
    trace_report = response.json()
    assert trace_report["incident_id"] == incident_id
    assert len(trace_report["wallets_identified"]) > 0
    assert trace_report["variant_analysis"]["is_decryptable"] is True  # Ryuk simulated to true
    
    # 3. Generate Compliance Report
    response = client.get(f"/api/ransomguard/compliance/{incident_id}")
    assert response.status_code == 200
    compliance = response.json()
    assert compliance["incident_id"] == incident_id
    assert "chain_of_custody_hash" in compliance

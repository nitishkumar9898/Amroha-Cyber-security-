import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finguard.db"
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

def test_finguard_flow():
    # 1. Transaction Anomaly
    response = client.post(
        "/api/finguard/detect-anomaly",
        json={
            "transaction_id": "TX-99901",
            "amount": 75000.0,
            "velocity_score": 12.5
        }
    )
    assert response.status_code == 200
    assert response.json()["is_anomalous"] is True
    assert "FRAUD_ALERT" in response.json()["action_taken"]

    # 2. Payment Trace (Crypto Cross-Border)
    response = client.post(
        "/api/finguard/trace-payment",
        json={
            "trace_id": "TRACE-XYZ",
            "hop_sequence": "UPI->CRYPTO_MIXER->SWIFT_CAYMAN"
        }
    )
    assert response.status_code == 200
    assert response.json()["crosses_borders"] is True
    assert "HIGH_COMPLEXITY" in response.json()["trace_status"]

    # 3. Laundering Pattern (Smurfing + Threat Intel)
    response = client.post(
        "/api/finguard/analyze-laundering",
        json={
            "entity_id": "ENTITY-404",
            "transaction_count": 60,
            "average_amount": 9500.0,
            "osint_threat_intel": True,
            "ransomware_watchlist": False
        }
    )
    assert response.status_code == 200
    assert "SMURFING" in response.json()["pattern_type"]
    assert "THREAT_INTEL_MATCH" in response.json()["pattern_type"]
    assert response.json()["risk_level"] == "CRITICAL"

    # 4. Compliance Report
    response = client.post(
        "/api/finguard/generate-compliance",
        json={
            "agency": "FIU-IND",
            "raw_financial_data": "{...suspicious activity report...}"
        }
    )
    assert response.status_code == 200
    assert "FIU-IND-" in response.json()["report_id"]
    assert len(response.json()["report_hash"]) == 64

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_netguard.db"
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

def test_netguard_flow():
    # 1. Register SCADA Node
    response = client.post(
        "/api/netguard/nodes",
        json={"node_name": "PLC-WaterValve", "node_type": "SCADA", "ip_address": "192.168.10.5"}
    )
    assert response.status_code == 200
    node_id = response.json()["id"]

    # 2. Analyze Traffic (Anomalous SCADA)
    response = client.post(
        "/api/netguard/analyze-traffic",
        json={
            "node_id": node_id,
            "protocol": "MODBUS",
            "bytes_transferred": 500,
            "payload_signature": "WRITE_REGISTER_UNAUTH_0x44"
        }
    )
    assert response.status_code == 200
    assert response.json()["is_anomalous"] is True
    assert response.json()["threat_type"] == "ICS_SABOTAGE"

    # 3. Register Telecom Node
    response = client.post(
        "/api/netguard/nodes",
        json={"node_name": "5G-Core-UPF", "node_type": "TELECOM", "ip_address": "10.0.0.5"}
    )
    assert response.status_code == 200
    telecom_node_id = response.json()["id"]

    # 4. Analyze Traffic (Cross-Slice Violation)
    response = client.post(
        "/api/netguard/analyze-traffic",
        json={
            "node_id": telecom_node_id,
            "protocol": "GTP-U",
            "bytes_transferred": 1500,
            "payload_signature": "CROSS_SLICE_EMBB_TO_URLLC"
        }
    )
    assert response.status_code == 200
    assert response.json()["is_anomalous"] is True
    assert response.json()["threat_type"] == "SLICE_ISOLATION_VIOLATION"

    # 5. Simulate APT Attack
    response = client.post(
        "/api/netguard/simulate-attack",
        json={
            "node_id": telecom_node_id,
            "simulation_type": "APT"
        }
    )
    assert response.status_code == 200
    assert response.json()["predicted_impact_hours"] == 72.0

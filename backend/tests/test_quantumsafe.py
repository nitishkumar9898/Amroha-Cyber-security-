import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_run_pqc_scan():
    payload = {
        "target_system": "Core Banking Gateway",
        "scan_id": str(uuid.uuid4())
    }
    response = client.post("/api/quantumsafe/scan", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["target_system"] == "Core Banking Gateway"
    assert len(data["assets"]) == 3
    
    # Check that RSA has vulnerability
    rsa_asset = next(a for a in data["assets"] if a["asset"]["algorithm"] == "RSA")
    assert rsa_asset["vulnerability"] is not None
    assert rsa_asset["vulnerability"]["criticality"] == "Critical"
    assert rsa_asset["migration"] is not None
    assert "Kyber" in rsa_asset["migration"]["recommended_pqc"]
    
    # Check that AES is quantum safe
    aes_asset = next(a for a in data["assets"] if a["asset"]["algorithm"] == "AES")
    assert aes_asset["asset"]["is_quantum_safe"] == True
    assert aes_asset["vulnerability"] is None

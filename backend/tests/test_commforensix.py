import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.fixture
def sample_message():
    return {
        "messages": [
            {
                "scan_id": "testscan1",
                "message_hash": "hash123",
                "sender_id": "alice",
                "receiver_id": "bob",
                "timestamp": "2026-01-01T12:00:00Z",
                "algorithm": "SignalProtocol",
                "key_size": 256,
                "is_quantum_safe": False,
            }
        ]
    }

def test_upload_messages(sample_message):
    response = client.post("/api/commforensix/messages", json=sample_message)
    assert response.status_code == 200
    data = response.json()
    assert data["scan_id"] == "testscan1"
    assert len(data["messages"]) == 1

def test_get_traffic():
    # Assuming scan_id exists from previous test (or use placeholder)
    response = client.get("/api/commforensix/traffic/testscan1")
    assert response.status_code == 200
    # Response schema may be empty list initially
    assert "patterns" in response.json()

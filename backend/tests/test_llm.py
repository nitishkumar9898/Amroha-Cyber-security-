import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_system_status():
    response = client.get("/api/sentinel/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "memory_entries" in data

def test_chat_fallback():
    # Will hit fallback mode unless GEMINI_API_KEY is set in the test env
    response = client.post("/api/chat?message=Hello+Sentinel")
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "intent" in data
    assert "threat_score" in data

def test_multimodal_fallback():
    response = client.post(
        "/api/sentinel/multimodal",
        data={"message": "Analyze this file"},
        files=[("files", ("test.txt", b"dummy content", "text/plain"))]
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "attachments_processed" in data
    assert data["attachments_processed"] == 1

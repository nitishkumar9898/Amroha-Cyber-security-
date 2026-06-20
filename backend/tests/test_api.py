import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Dynamically import the FastAPI app
app_path = Path(__file__).resolve().parents[2] / "backend" / "app" / "main.py"
import importlib.util
spec = importlib.util.spec_from_file_location("backend.app.main", app_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = app_module.app

client = TestClient(app)

@pytest.fixture
def auth_header():
    # Placeholder: generate JWT or API key for authenticated routes
    return {"Authorization": "Bearer dummy-token"}

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "modules_loaded" in data

def test_invalid_route():
    response = client.get("/nonexistent")
    assert response.status_code == 404

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_health_endpoint_returns_200(client):
    """Health endpoint should return 200 OK."""
    response = client.get("/live")
    assert response.status_code == 200


def test_health_endpoint_returns_healthy_status(client):
    """Health endpoint should return healthy status."""
    response = client.get("/live")
    data = response.json()
    assert data["status"] == "healthy"


def test_health_endpoint_contains_version(client):
    """Health endpoint should include version."""
    response = client.get("/live")
    data = response.json()
    assert "version" in data
    assert data["version"] == "0.2.0"


def test_health_endpoint_contains_service_name(client):
    """Health endpoint should identify the service."""
    response = client.get("/live")
    data = response.json()
    assert "service" in data
    assert "transaction-risk-scoring-api" in data["service"]

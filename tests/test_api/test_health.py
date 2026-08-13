import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_health_endpoint_returns_200(client):
    """Health endpoint should return 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_healthy_status(client):
    """Health endpoint should return healthy status."""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"


def test_health_endpoint_contains_version(client):
    """Health endpoint should include version."""
    response = client.get("/health")
    data = response.json()
    assert "version" in data
    assert data["version"] == "0.1.0"


def test_health_endpoint_contains_service_name(client):
    """Health endpoint should identify the service."""
    response = client.get("/health")
    data = response.json()
    assert "service" in data
    assert "transaction-risk-scoring-api" in data["service"]


def test_score_endpoint_not_yet_implemented(client):
    """POST /score should return 501 (not implemented)."""
    response = client.post("/score", json={
        "user_id": "test",
        "amount": 100.0,
        "timestamp": "2024-01-15T10:00:00",
        "merchant_category": "grocery",
        "location": "40.7128,-74.0060",
    })
    assert response.status_code == 501
    data = response.json()
    assert "Coming in Phase 2" in data.get("error", "")


def test_get_transactions_not_yet_implemented(client):
    """GET /transactions should return 501 (not implemented)."""
    response = client.get("/transactions")
    assert response.status_code == 501


def test_get_transaction_detail_not_yet_implemented(client):
    """GET /transactions/{id} should return 501 (not implemented)."""
    response = client.get("/transactions/123")
    assert response.status_code == 501

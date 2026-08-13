import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db, APIKey


@pytest.fixture
def test_engine():
    """Create test engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db(test_engine):
    """Create in-memory SQLite database for tests."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        database = TestingSessionLocal()
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(db):
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def api_key(test_engine):
    """Create a test API key."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db_session = SessionLocal()

    key = APIKey(name="test_key", key=APIKey.generate_key())
    db_session.add(key)
    db_session.commit()
    db_session.refresh(key)
    db_session.close()

    return key.key


class TestScoreEndpoint:
    def test_score_valid_transaction(self, client, api_key):
        """POST /api/v1/score should accept valid transaction."""
        response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_123"
        assert data["amount"] == 100.0
        assert 0 <= data["risk_score"] <= 100
        assert data["severity"] in ["low", "medium", "high"]
        assert "rules_triggered" in data

    def test_score_high_risk_category(self, client):
        """POST /api/v1/score should flag high-risk categories."""
        response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_456",
                "amount": 500.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "cryptocurrency_exchange",
                "location": "40.7128,-74.0060",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["risk_score"] > 0
        triggered_rules = [r["name"] for r in data["rules_triggered"] if r["triggered"]]
        assert "high_risk_category_check" in triggered_rules

    def test_score_invalid_amount(self, client):
        """POST /api/v1/score should reject negative amount."""
        response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": -100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
        )
        assert response.status_code == 422

    def test_score_invalid_timestamp(self, client):
        """POST /api/v1/score should reject invalid timestamp."""
        response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "invalid-date",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
        )
        assert response.status_code == 422

    def test_score_invalid_location(self, client):
        """POST /api/v1/score should reject invalid location format."""
        response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "grocery",
                "location": "invalid",
            },
        )
        assert response.status_code == 422


class TestListTransactions:
    def test_list_empty(self, client):
        """GET /api/v1/transactions should return empty list initially."""
        response = client.get("/api/v1/transactions")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_after_score(self, client):
        """GET /api/v1/transactions should return scored transactions."""
        # Score a transaction
        client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
        )

        # List transactions
        response = client.get("/api/v1/transactions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == "user_123"
        assert data[0]["severity"] in ["low", "medium", "high"]

    def test_list_filter_by_severity(self, client):
        """GET /api/v1/transactions should filter by severity."""
        # Score a low-risk transaction
        client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
        )

        # Score a high-risk transaction
        client.post(
            "/api/v1/score",
            json={
                "user_id": "user_456",
                "amount": 500.0,
                "timestamp": "2024-01-15T10:05:00",
                "merchant_category": "cryptocurrency_exchange",
                "location": "40.7128,-74.0060",
            },
        )

        # Filter by high severity
        response = client.get("/api/v1/transactions?severity=high")
        assert response.status_code == 200
        data = response.json()
        assert all(t["severity"] == "high" for t in data)

    def test_list_filter_by_user_id(self, client):
        """GET /api/v1/transactions should filter by user_id."""
        # Score for multiple users
        client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
        )
        client.post(
            "/api/v1/score",
            json={
                "user_id": "user_456",
                "amount": 200.0,
                "timestamp": "2024-01-15T10:05:00",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
        )

        # Filter by user
        response = client.get("/api/v1/transactions?user_id=user_123")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == "user_123"


class TestGetTransaction:
    def test_get_transaction_not_found(self, client):
        """GET /api/v1/transactions/{id} should return 404 for missing ID."""
        response = client.get("/api/v1/transactions/9999")
        assert response.status_code == 404

    def test_get_transaction_details(self, client):
        """GET /api/v1/transactions/{id} should return full details."""
        # Score a transaction
        score_response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
        )
        transaction_id = score_response.json()["id"]

        # Get transaction details
        response = client.get(f"/api/v1/transactions/{transaction_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction_id
        assert data["user_id"] == "user_123"
        assert data["location"] == "40.7128,-74.0060"
        assert "rules_triggered" in data
        assert len(data["rules_triggered"]) == 5  # All 5 rules evaluated

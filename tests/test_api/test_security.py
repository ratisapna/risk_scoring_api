import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db, APIKey
from app.db.rate_limit import RateLimitLog


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


class TestAPIKeyAuthentication:
    def test_missing_api_key(self, client):
        """Request without API key should return 401."""
        response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
        )
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    def test_invalid_api_key(self, client):
        """Request with invalid API key should return 401."""
        response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
            headers={"Authorization": "Bearer invalid_key"},
        )
        assert response.status_code == 401
        assert "Invalid or inactive API key" in response.json()["detail"]

    def test_invalid_auth_header(self, client):
        """Request with invalid auth header should return 401."""
        response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
            headers={"Authorization": "InvalidHeader"},
        )
        assert response.status_code == 401
        assert "Invalid authorization header" in response.json()["detail"]


class TestMerchantCategoryValidation:
    def test_invalid_merchant_category(self, client, api_key):
        """Invalid merchant category should return 422."""
        response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "invalid_category",
                "location": "40.7128,-74.0060",
            },
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 422

    def test_valid_merchant_categories(self, client, api_key):
        """Valid merchant categories should be accepted."""
        valid_categories = [
            "grocery", "restaurant", "retail", "cryptocurrency_exchange",
            "gambling", "wire_transfer", "money_remittance"
        ]
        for category in valid_categories:
            response = client.post(
                "/api/v1/score",
                json={
                    "user_id": "user_123",
                    "amount": 100.0,
                    "timestamp": "2024-01-15T10:00:00",
                    "merchant_category": category,
                    "location": "40.7128,-74.0060",
                },
                headers={"Authorization": f"Bearer {api_key}"},
            )
            assert response.status_code == 200, f"Failed for category: {category}"

    def test_case_insensitive_category(self, client, api_key):
        """Merchant category should be case-insensitive."""
        response = client.post(
            "/api/v1/score",
            json={
                "user_id": "user_123",
                "amount": 100.0,
                "timestamp": "2024-01-15T10:00:00",
                "merchant_category": "GROCERY",
                "location": "40.7128,-74.0060",
            },
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200

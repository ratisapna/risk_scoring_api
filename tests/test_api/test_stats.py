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


def test_stats_endpoint_requires_auth(client):
    """Stats endpoint should require authentication."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 401


def test_stats_endpoint_with_no_transactions(client, api_key):
    """Stats endpoint should return zeros for no transactions."""
    response = client.get("/api/v1/stats", headers={"Authorization": f"Bearer {api_key}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] == 0
    assert data["high_risk_count"] == 0
    assert data["medium_risk_count"] == 0
    assert data["low_risk_count"] == 0
    assert data["high_risk_percentage"] == 0


def test_stats_endpoint_with_transactions(client, api_key):
    """Stats endpoint should return accurate statistics."""
    headers = {"Authorization": f"Bearer {api_key}"}

    # Score multiple transactions
    client.post(
        "/api/v1/score",
        json={
            "user_id": "user_1",
            "amount": 100.0,
            "timestamp": "2024-08-13T10:00:00",
            "merchant_category": "grocery",
            "location": "40.7128,-74.0060",
        },
        headers=headers,
    )

    client.post(
        "/api/v1/score",
        json={
            "user_id": "user_2",
            "amount": 500.0,
            "timestamp": "2024-08-13T11:00:00",
            "merchant_category": "cryptocurrency_exchange",
            "location": "40.7128,-74.0060",
        },
        headers=headers,
    )

    # Get stats
    response = client.get("/api/v1/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] == 2
    assert data["high_risk_count"] == 1
    assert data["low_risk_count"] == 1

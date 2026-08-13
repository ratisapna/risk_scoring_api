import pytest
from datetime import datetime, timedelta


@pytest.fixture
def base_transaction():
    """Base transaction object for testing."""
    return {
        "user_id": "user_123",
        "amount": 100.0,
        "timestamp": "2024-01-15T10:00:00",
        "merchant_category": "grocery",
        "location": "40.7128,-74.0060",  # NYC coordinates
    }


@pytest.fixture
def empty_user_history():
    """User with no transaction history."""
    return {
        "recent_transactions": [],
        "avg_transaction_amount": 0,
        "historical_amounts": [],
    }


@pytest.fixture
def normal_user_history():
    """User with normal transaction history."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    return {
        "recent_transactions": [
            {
                "user_id": "user_123",
                "amount": 75.0,
                "timestamp": (base_time - timedelta(hours=2)).isoformat(),
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
            {
                "user_id": "user_123",
                "amount": 80.0,
                "timestamp": (base_time - timedelta(hours=1)).isoformat(),
                "merchant_category": "restaurant",
                "location": "40.7128,-74.0060",
            },
        ],
        "avg_transaction_amount": 77.5,
        "historical_amounts": [75.0, 80.0, 72.0, 85.0, 78.0],
        "account_creation_date": (base_time - timedelta(days=180)).isoformat(),
    }


@pytest.fixture
def high_velocity_history():
    """User with multiple transactions in short time window."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    recent = []
    for i in range(6):
        recent.append(
            {
                "user_id": "user_456",
                "amount": 50.0,
                "timestamp": (base_time - timedelta(minutes=9 - i)).isoformat(),
                "merchant_category": "retail",
                "location": "40.7128,-74.0060",
            }
        )
    return {
        "recent_transactions": recent,
        "avg_transaction_amount": 50.0,
        "historical_amounts": [50.0] * 10,
        "account_creation_date": (base_time - timedelta(days=90)).isoformat(),
    }


@pytest.fixture
def new_account_history():
    """User with recently created account."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    return {
        "recent_transactions": [],
        "avg_transaction_amount": 0,
        "historical_amounts": [],
        "account_creation_date": (base_time - timedelta(days=5)).isoformat(),
    }


@pytest.fixture
def long_distance_history():
    """User history with last transaction far away."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    return {
        "recent_transactions": [],
        "avg_transaction_amount": 100.0,
        "historical_amounts": [100.0],
        "account_creation_date": (base_time - timedelta(days=90)).isoformat(),
        "last_transaction_location": "51.5074,-0.1278",  # London
        "last_transaction_time": base_time - timedelta(hours=1),
    }

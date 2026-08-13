from datetime import datetime, timedelta
import pytest
from app.rules.velocity import check_velocity


def test_velocity_no_history(base_transaction, empty_user_history):
    """Velocity check should not trigger with no history."""
    result = check_velocity(base_transaction, empty_user_history)
    assert result.triggered is False
    assert result.weight == 0
    assert "No recent" in result.reason


def test_velocity_below_threshold(base_transaction):
    """Velocity check should not trigger below threshold."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "recent_transactions": [
            {
                "user_id": "user_123",
                "amount": 75.0,
                "timestamp": (base_time - timedelta(minutes=2)).isoformat(),
                "merchant_category": "grocery",
                "location": "40.7128,-74.0060",
            },
            {
                "user_id": "user_123",
                "amount": 80.0,
                "timestamp": (base_time - timedelta(minutes=1)).isoformat(),
                "merchant_category": "restaurant",
                "location": "40.7128,-74.0060",
            },
        ]
    }
    result = check_velocity(base_transaction, history)
    assert result.triggered is False
    assert result.weight == 0
    assert "Only 2 transactions" in result.reason


def test_velocity_exceeds_threshold(base_transaction, high_velocity_history):
    """Velocity check should trigger with 6 transactions in 10 minutes."""
    result = check_velocity(base_transaction, high_velocity_history)
    assert result.triggered is True
    assert result.weight == 30
    assert "6 transactions in last 10 minutes" in result.reason


def test_velocity_exactly_at_threshold(base_transaction):
    """Velocity check at exactly 5 transactions should trigger."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "recent_transactions": [
            {
                "user_id": "user_123",
                "amount": 50.0,
                "timestamp": (base_time - timedelta(minutes=i+1)).isoformat(),
                "merchant_category": "retail",
                "location": "40.7128,-74.0060",
            }
            for i in range(5)
        ]
    }
    result = check_velocity(base_transaction, history)
    assert result.triggered is True
    assert result.weight == 30
    assert "5 transactions" in result.reason


def test_velocity_transactions_outside_window(base_transaction):
    """Velocity check should exclude transactions outside 10-minute window."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "recent_transactions": [
            {
                "user_id": "user_123",
                "amount": 50.0,
                "timestamp": (base_time - timedelta(minutes=15)).isoformat(),
                "merchant_category": "retail",
                "location": "40.7128,-74.0060",
            },
            {
                "user_id": "user_123",
                "amount": 50.0,
                "timestamp": (base_time - timedelta(minutes=1)).isoformat(),
                "merchant_category": "retail",
                "location": "40.7128,-74.0060",
            },
        ]
    }
    transaction = {
        "user_id": "user_123",
        "amount": 100.0,
        "timestamp": base_time.isoformat(),
        "merchant_category": "grocery",
        "location": "40.7128,-74.0060",
    }
    result = check_velocity(transaction, history)
    assert result.triggered is False
    assert "Only 1 transactions" in result.reason

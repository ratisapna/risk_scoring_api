from datetime import datetime, timedelta
import pytest
from app.rules.impossible_travel import check_impossible_travel


def test_impossible_travel_no_history(base_transaction, empty_user_history):
    """Impossible travel check should not trigger with no location history."""
    result = check_impossible_travel(base_transaction, empty_user_history)
    assert result.triggered is False
    assert result.weight == 0
    assert "No previous" in result.reason


def test_impossible_travel_no_current_location():
    """Impossible travel check should handle missing current location."""
    transaction = {
        "user_id": "user_123",
        "amount": 100.0,
        "timestamp": "2024-01-15T10:00:00",
        "merchant_category": "grocery",
        "location": None,
    }
    history = {
        "last_transaction_location": "40.7128,-74.0060",
        "last_transaction_time": datetime(2024, 1, 15, 9, 0, 0),
    }
    result = check_impossible_travel(transaction, history)
    assert result.triggered is False
    assert "no location data" in result.reason


def test_impossible_travel_feasible(base_transaction, long_distance_history):
    """Feasible travel (NYC to London in 8 hours via flight) should not trigger."""
    transaction = dict(base_transaction)
    transaction["location"] = "51.5074,-0.1278"  # London
    transaction["timestamp"] = "2024-01-15T18:00:00"
    result = check_impossible_travel(transaction, long_distance_history)
    assert result.triggered is False
    assert result.weight == 0


def test_impossible_travel_impossible(base_transaction):
    """Impossible travel (NYC to London in 1 hour) should trigger."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "last_transaction_location": "40.7128,-74.0060",  # NYC
        "last_transaction_time": base_time - timedelta(hours=1),
    }
    transaction = dict(base_transaction)
    transaction["location"] = "51.5074,-0.1278"  # London
    transaction["timestamp"] = base_time.isoformat()
    result = check_impossible_travel(transaction, history)
    assert result.triggered is True
    assert result.weight == 40
    assert "km/h" in result.reason


def test_impossible_travel_same_location(base_transaction, normal_user_history):
    """Same location transactions should never trigger."""
    transaction = dict(base_transaction)
    transaction["timestamp"] = "2024-01-15T10:30:00"
    history = dict(normal_user_history)
    history["last_transaction_location"] = "40.7128,-74.0060"
    history["last_transaction_time"] = datetime(2024, 1, 15, 10, 0, 0)
    result = check_impossible_travel(transaction, history)
    assert result.triggered is False
    assert "feasible" in result.reason


def test_impossible_travel_invalid_coordinates():
    """Invalid coordinates should be handled gracefully."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "last_transaction_location": "invalid",
        "last_transaction_time": base_time - timedelta(hours=1),
    }
    transaction = {
        "user_id": "user_123",
        "amount": 100.0,
        "timestamp": base_time.isoformat(),
        "merchant_category": "grocery",
        "location": "40.7128,-74.0060",
    }
    result = check_impossible_travel(transaction, history)
    assert result.triggered is False
    assert "Could not evaluate" in result.reason


def test_impossible_travel_time_order():
    """Transactions before previous transaction should be flagged as data issue."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "last_transaction_location": "40.7128,-74.0060",
        "last_transaction_time": base_time,
    }
    transaction = {
        "user_id": "user_123",
        "amount": 100.0,
        "timestamp": (base_time - timedelta(hours=1)).isoformat(),
        "merchant_category": "grocery",
        "location": "40.7128,-74.0060",
    }
    result = check_impossible_travel(transaction, history)
    assert result.triggered is False
    assert "data issue" in result.reason

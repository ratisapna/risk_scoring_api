from datetime import datetime, timedelta
import pytest
from app.rules.new_account import check_new_account_high_value


def test_new_account_no_creation_date(base_transaction, empty_user_history):
    """New account check should not trigger without creation date."""
    result = check_new_account_high_value(base_transaction, empty_user_history)
    assert result.triggered is False
    assert result.weight == 0
    assert "No account creation" in result.reason


def test_new_account_high_value_triggers(base_transaction, new_account_history):
    """New account with high-value transaction should trigger."""
    transaction = dict(base_transaction)
    transaction["amount"] = 1500.0
    result = check_new_account_high_value(transaction, new_account_history)
    assert result.triggered is True
    assert result.weight == 20
    assert "5 days old" in result.reason
    assert "high-value" in result.reason


def test_new_account_low_value_no_trigger(base_transaction, new_account_history):
    """New account with low-value transaction should not trigger."""
    transaction = dict(base_transaction)
    transaction["amount"] = 50.0
    result = check_new_account_high_value(transaction, new_account_history)
    assert result.triggered is False
    assert result.weight == 0
    assert "below threshold" in result.reason


def test_old_account_high_value_no_trigger(base_transaction, normal_user_history):
    """Old account with high-value transaction should not trigger."""
    transaction = dict(base_transaction)
    transaction["amount"] = 2000.0
    result = check_new_account_high_value(transaction, normal_user_history)
    assert result.triggered is False
    assert result.weight == 0
    assert "exceeds new account threshold" in result.reason


def test_new_account_threshold_boundary(base_transaction):
    """Test exactly at $1000 threshold."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "account_creation_date": (base_time - timedelta(days=5)).isoformat(),
    }
    transaction = dict(base_transaction)
    transaction["timestamp"] = base_time.isoformat()
    transaction["amount"] = 1000.0
    result = check_new_account_high_value(transaction, history)
    assert result.triggered is False


def test_new_account_threshold_just_above(base_transaction):
    """Test just above $1000 threshold."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "account_creation_date": (base_time - timedelta(days=5)).isoformat(),
    }
    transaction = dict(base_transaction)
    transaction["timestamp"] = base_time.isoformat()
    transaction["amount"] = 1000.01
    result = check_new_account_high_value(transaction, history)
    assert result.triggered is True
    assert result.weight == 20


def test_new_account_age_boundary_30_days(base_transaction):
    """Test account exactly 30 days old."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "account_creation_date": (base_time - timedelta(days=30)).isoformat(),
    }
    transaction = dict(base_transaction)
    transaction["timestamp"] = base_time.isoformat()
    transaction["amount"] = 2000.0
    result = check_new_account_high_value(transaction, history)
    assert result.triggered is False


def test_new_account_age_boundary_29_days(base_transaction):
    """Test account 29 days old (should be considered new)."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "account_creation_date": (base_time - timedelta(days=29)).isoformat(),
    }
    transaction = dict(base_transaction)
    transaction["timestamp"] = base_time.isoformat()
    transaction["amount"] = 2000.0
    result = check_new_account_high_value(transaction, history)
    assert result.triggered is True
    assert result.weight == 20


def test_new_account_datetime_object():
    """Test with datetime object instead of ISO string."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    history = {
        "account_creation_date": base_time - timedelta(days=5),
    }
    transaction = {
        "user_id": "user_123",
        "amount": 1500.0,
        "timestamp": base_time.isoformat(),
        "merchant_category": "grocery",
        "location": "40.7128,-74.0060",
    }
    result = check_new_account_high_value(transaction, history)
    assert result.triggered is True
    assert result.weight == 20

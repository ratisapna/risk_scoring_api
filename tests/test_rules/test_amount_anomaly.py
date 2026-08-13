import pytest
from app.rules.amount_anomaly import check_amount_anomaly


def test_amount_anomaly_no_history(base_transaction, empty_user_history):
    """Amount check should not trigger without historical data."""
    result = check_amount_anomaly(base_transaction, empty_user_history)
    assert result.triggered is False
    assert result.weight == 0
    assert "No historical" in result.reason


def test_amount_anomaly_3x_threshold(base_transaction):
    """Amount check should trigger if 3x user average."""
    history = {
        "avg_transaction_amount": 100.0,
        "historical_amounts": [100.0, 95.0, 105.0, 98.0],
    }
    transaction = dict(base_transaction)
    transaction["amount"] = 300.0
    result = check_amount_anomaly(transaction, history)
    assert result.triggered is True
    assert result.weight == 35
    assert "3.0x" in result.reason


def test_amount_anomaly_below_3x_threshold(base_transaction):
    """Amount check should not trigger below 3x threshold with realistic variance."""
    history = {
        "avg_transaction_amount": 100.0,
        "historical_amounts": [50.0, 75.0, 100.0, 125.0, 150.0, 100.0, 110.0],
    }
    transaction = dict(base_transaction)
    transaction["amount"] = 150.0
    result = check_amount_anomaly(transaction, history)
    assert result.triggered is False
    assert result.weight == 0


def test_amount_anomaly_z_score_high(base_transaction):
    """Amount check should trigger on 2-sigma outlier."""
    history = {
        "avg_transaction_amount": 100.0,
        "historical_amounts": [100.0, 98.0, 102.0, 99.0, 101.0],
    }
    transaction = dict(base_transaction)
    transaction["amount"] = 130.0
    result = check_amount_anomaly(transaction, history)
    assert result.triggered is True
    assert result.weight == 35
    assert "sigma" in result.reason


def test_amount_anomaly_z_score_within_range(base_transaction):
    """Amount check should not trigger within 2-sigma."""
    history = {
        "avg_transaction_amount": 100.0,
        "historical_amounts": [90.0, 95.0, 100.0, 105.0, 110.0],
    }
    transaction = dict(base_transaction)
    transaction["amount"] = 115.0
    result = check_amount_anomaly(transaction, history)
    assert result.triggered is False
    assert result.weight == 0


def test_amount_anomaly_insufficient_history(base_transaction):
    """Amount check with only 1 historical value should use multiplier."""
    history = {
        "avg_transaction_amount": 100.0,
        "historical_amounts": [100.0],
    }
    transaction = dict(base_transaction)
    transaction["amount"] = 250.0
    result = check_amount_anomaly(transaction, history)
    assert result.triggered is False
    assert "2.5x average" in result.reason


def test_amount_anomaly_edge_case_zero_std_dev(base_transaction):
    """Amount check should handle zero standard deviation."""
    history = {
        "avg_transaction_amount": 100.0,
        "historical_amounts": [100.0, 100.0, 100.0, 100.0],
    }
    transaction = dict(base_transaction)
    transaction["amount"] = 150.0
    result = check_amount_anomaly(transaction, history)
    assert result.triggered is False
    assert result.weight == 0

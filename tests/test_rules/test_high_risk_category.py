import pytest
from app.rules.high_risk_category import check_high_risk_category


def test_high_risk_category_gift_cards(base_transaction):
    """Gift card transactions should trigger."""
    transaction = dict(base_transaction)
    transaction["merchant_category"] = "gift_cards"
    result = check_high_risk_category(transaction)
    assert result.triggered is True
    assert result.weight == 25
    assert "high-risk" in result.reason


def test_high_risk_category_crypto(base_transaction):
    """Cryptocurrency exchange transactions should trigger."""
    transaction = dict(base_transaction)
    transaction["merchant_category"] = "cryptocurrency_exchange"
    result = check_high_risk_category(transaction)
    assert result.triggered is True
    assert result.weight == 25


def test_high_risk_category_wire_transfer(base_transaction):
    """Wire transfer transactions should trigger."""
    transaction = dict(base_transaction)
    transaction["merchant_category"] = "wire_transfer"
    result = check_high_risk_category(transaction)
    assert result.triggered is True
    assert result.weight == 25


def test_high_risk_category_gambling(base_transaction):
    """Gambling transactions should trigger."""
    transaction = dict(base_transaction)
    transaction["merchant_category"] = "gambling"
    result = check_high_risk_category(transaction)
    assert result.triggered is True
    assert result.weight == 25


def test_high_risk_category_money_remittance(base_transaction):
    """Money remittance transactions should trigger."""
    transaction = dict(base_transaction)
    transaction["merchant_category"] = "money_remittance"
    result = check_high_risk_category(transaction)
    assert result.triggered is True
    assert result.weight == 25


def test_high_risk_category_prepaid_cards(base_transaction):
    """Prepaid card transactions should trigger."""
    transaction = dict(base_transaction)
    transaction["merchant_category"] = "prepaid_cards"
    result = check_high_risk_category(transaction)
    assert result.triggered is True
    assert result.weight == 25


def test_high_risk_category_high_value_goods(base_transaction):
    """High value goods transactions should trigger."""
    transaction = dict(base_transaction)
    transaction["merchant_category"] = "high_value_goods"
    result = check_high_risk_category(transaction)
    assert result.triggered is True
    assert result.weight == 25


def test_safe_category_grocery(base_transaction):
    """Grocery transactions should not trigger."""
    result = check_high_risk_category(base_transaction)
    assert result.triggered is False
    assert result.weight == 0
    assert "acceptable" in result.reason


def test_safe_category_restaurant(base_transaction):
    """Restaurant transactions should not trigger."""
    transaction = dict(base_transaction)
    transaction["merchant_category"] = "restaurant"
    result = check_high_risk_category(transaction)
    assert result.triggered is False
    assert result.weight == 0


def test_safe_category_retail(base_transaction):
    """Retail transactions should not trigger."""
    transaction = dict(base_transaction)
    transaction["merchant_category"] = "retail"
    result = check_high_risk_category(transaction)
    assert result.triggered is False
    assert result.weight == 0


def test_high_risk_category_case_insensitive(base_transaction):
    """Category check should be case-insensitive."""
    transaction = dict(base_transaction)
    transaction["merchant_category"] = "GIFT_CARDS"
    result = check_high_risk_category(transaction)
    assert result.triggered is True
    assert result.weight == 25


def test_high_risk_category_missing_field():
    """Transaction without category field should not trigger."""
    transaction = {
        "user_id": "user_123",
        "amount": 100.0,
        "timestamp": "2024-01-15T10:00:00",
        "location": "40.7128,-74.0060",
    }
    result = check_high_risk_category(transaction)
    assert result.triggered is False
    assert result.weight == 0

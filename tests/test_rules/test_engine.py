from datetime import datetime, timedelta
import pytest
from app.rules.models import RuleResult, ScoringResult
from app.rules.engine import aggregate_scores, score_transaction


class TestAggregateScores:
    def test_no_rules_triggered(self):
        """No triggered rules should result in low risk."""
        results = [
            RuleResult("rule1", False, "Not triggered", 30),
            RuleResult("rule2", False, "Not triggered", 25),
        ]
        score = aggregate_scores(results)
        assert score.risk_score == 0
        assert score.severity == "low"
        assert len(score.rules_triggered) == 2

    def test_single_rule_triggered(self):
        """Single triggered rule should use its weight."""
        results = [
            RuleResult("rule1", True, "Triggered", 35),
            RuleResult("rule2", False, "Not triggered", 25),
        ]
        score = aggregate_scores(results)
        assert score.risk_score == 35
        assert score.severity == "medium"

    def test_multiple_rules_triggered(self):
        """Multiple triggered rules should sum weights."""
        results = [
            RuleResult("rule1", True, "Triggered", 35),
            RuleResult("rule2", True, "Triggered", 30),
            RuleResult("rule3", False, "Not triggered", 20),
        ]
        score = aggregate_scores(results)
        assert score.risk_score == 65
        assert score.severity == "medium"

    def test_score_capped_at_100(self):
        """Score should be capped at 100."""
        results = [
            RuleResult("rule1", True, "Triggered", 50),
            RuleResult("rule2", True, "Triggered", 40),
            RuleResult("rule3", True, "Triggered", 30),
        ]
        score = aggregate_scores(results)
        assert score.risk_score == 100
        assert score.severity == "high"

    def test_severity_low_boundary(self):
        """Score of 33 should be low."""
        results = [RuleResult("rule1", True, "Triggered", 33)]
        score = aggregate_scores(results)
        assert score.severity == "low"

    def test_severity_medium_boundary(self):
        """Score of 34 should be medium."""
        results = [RuleResult("rule1", True, "Triggered", 34)]
        score = aggregate_scores(results)
        assert score.severity == "medium"

    def test_severity_high_boundary(self):
        """Score of 67 should be high."""
        results = [
            RuleResult("rule1", True, "Triggered", 40),
            RuleResult("rule2", True, "Triggered", 27),
        ]
        score = aggregate_scores(results)
        assert score.severity == "high"

    def test_to_dict_serialization(self):
        """Scoring result should serialize to dict."""
        results = [RuleResult("rule1", True, "Triggered", 35)]
        score = aggregate_scores(results)
        d = score.to_dict()
        assert d["risk_score"] == 35
        assert d["severity"] == "medium"
        assert len(d["rules_triggered"]) == 1
        assert d["rules_triggered"][0]["triggered"] is True


class TestScoreTransaction:
    def test_score_with_no_history(self, base_transaction, empty_user_history):
        """Scoring with minimal history should work."""
        result = score_transaction(base_transaction, empty_user_history)
        assert result.risk_score == 0
        assert result.severity == "low"
        assert len(result.rules_triggered) == 5

    def test_score_with_full_history(self, base_transaction, normal_user_history):
        """Scoring with full history should work."""
        result = score_transaction(base_transaction, normal_user_history)
        assert isinstance(result, ScoringResult)
        assert 0 <= result.risk_score <= 100
        assert result.severity in ["low", "medium", "high"]

    def test_score_high_risk_transaction(self):
        """Multiple rules triggering should produce high score."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        transaction = {
            "user_id": "user_123",
            "amount": 5000.0,  # High amount
            "timestamp": base_time.isoformat(),
            "merchant_category": "cryptocurrency_exchange",  # High risk category
            "location": "51.5074,-0.1278",  # London
        }
        history = {
            "recent_transactions": [
                {
                    "user_id": "user_123",
                    "amount": 100.0,
                    "timestamp": (base_time - timedelta(minutes=2)).isoformat(),
                    "merchant_category": "grocery",
                    "location": "51.5074,-0.1278",
                },
            ] * 5,  # Velocity trigger
            "avg_transaction_amount": 100.0,
            "historical_amounts": [100.0] * 5,
            "account_creation_date": (base_time - timedelta(days=5)).isoformat(),  # New account
            "last_transaction_location": "40.7128,-74.0060",  # NYC
            "last_transaction_time": base_time - timedelta(hours=1),
        }
        result = score_transaction(transaction, history)
        assert result.risk_score > 50
        assert result.severity in ["medium", "high"]
        triggered_names = [r.name for r in result.rules_triggered if r.triggered]
        # Should trigger multiple rules
        assert len(triggered_names) > 1

    def test_score_low_risk_transaction(self):
        """Normal transaction with old account should score low."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        transaction = {
            "user_id": "user_123",
            "amount": 50.0,
            "timestamp": base_time.isoformat(),
            "merchant_category": "grocery",
            "location": "40.7128,-74.0060",
        }
        history = {
            "recent_transactions": [],
            "avg_transaction_amount": 100.0,
            "historical_amounts": [90.0, 95.0, 105.0, 110.0],
            "account_creation_date": (base_time - timedelta(days=365)).isoformat(),
        }
        result = score_transaction(transaction, history)
        assert result.risk_score <= 33
        assert result.severity == "low"

    def test_score_without_history(self, base_transaction):
        """Scoring should work without user history parameter."""
        result = score_transaction(base_transaction)
        assert isinstance(result, ScoringResult)
        assert 0 <= result.risk_score <= 100

    def test_all_rules_included(self, base_transaction, normal_user_history):
        """All five rules should be evaluated."""
        result = score_transaction(base_transaction, normal_user_history)
        rule_names = {r.name for r in result.rules_triggered}
        assert "velocity_check" in rule_names
        assert "amount_anomaly_check" in rule_names
        assert "impossible_travel_check" in rule_names
        assert "high_risk_category_check" in rule_names
        assert "new_account_high_value_check" in rule_names
        assert len(rule_names) == 5

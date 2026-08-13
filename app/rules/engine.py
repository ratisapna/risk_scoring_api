from datetime import datetime
from typing import Optional

from app.rules.models import RuleResult, ScoringResult
from app.rules.velocity import check_velocity
from app.rules.amount_anomaly import check_amount_anomaly
from app.rules.impossible_travel import check_impossible_travel
from app.rules.high_risk_category import check_high_risk_category
from app.rules.new_account import check_new_account_high_value


def aggregate_scores(results: list[RuleResult]) -> ScoringResult:
    """Aggregate individual rule results into a final risk score.

    Score calculation:
    - Each triggered rule contributes its weight (0-100)
    - Maximum score is 100 (if multiple rules trigger, cap at 100)
    - Severity labels: low (0-33), medium (34-66), high (67-100)
    """
    triggered_rules = [r for r in results if r.triggered]
    weights_sum = sum(r.weight for r in triggered_rules)
    risk_score = min(100, weights_sum)

    if risk_score <= 33:
        severity = "low"
    elif risk_score <= 66:
        severity = "medium"
    else:
        severity = "high"

    return ScoringResult(
        risk_score=risk_score,
        severity=severity,
        rules_triggered=results,
    )


def score_transaction(
    transaction: dict,
    user_history: Optional[dict] = None,
) -> ScoringResult:
    """Score a single transaction through all rules.

    Args:
        transaction: dict with keys: user_id, amount, timestamp, merchant_category, location
        user_history: optional dict with historical context:
            - recent_transactions: list of recent transaction dicts
            - avg_transaction_amount: float
            - account_creation_date: datetime
            - last_transaction_location: str (lat,lon format)
            - last_transaction_time: datetime

    Returns:
        ScoringResult with aggregated score and triggered rules
    """
    if user_history is None:
        user_history = {}

    results = [
        check_velocity(transaction, user_history),
        check_amount_anomaly(transaction, user_history),
        check_impossible_travel(transaction, user_history),
        check_high_risk_category(transaction),
        check_new_account_high_value(transaction, user_history),
    ]

    return aggregate_scores(results)

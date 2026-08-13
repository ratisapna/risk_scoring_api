from statistics import stdev
from app.rules.models import RuleResult


def check_amount_anomaly(transaction: dict, user_history: dict) -> RuleResult:
    """Check if transaction amount is an anomaly relative to user's history.

    Rule: Flag if amount is 3x the user's average historical transaction, or
           if it's a 2-sigma outlier (assuming normal distribution).
    Weight: 35 points if triggered.
    """
    avg_amount = user_history.get("avg_transaction_amount", 0)
    historical_amounts = user_history.get("historical_amounts", [])

    if avg_amount == 0:
        return RuleResult(
            name="amount_anomaly_check",
            triggered=False,
            reason="No historical transaction data",
            weight=0,
        )

    current_amount = float(transaction["amount"])
    multiplier = current_amount / avg_amount

    triggered = False
    reason = ""

    if multiplier >= 3.0:
        triggered = True
        reason = f"Amount ${current_amount:.2f} is {multiplier:.1f}x user's average (${avg_amount:.2f})"
    elif len(historical_amounts) >= 2:
        try:
            std_dev = stdev(historical_amounts)
            z_score = (current_amount - avg_amount) / std_dev if std_dev > 0 else 0
            if z_score >= 2.0:
                triggered = True
                reason = f"Amount ${current_amount:.2f} is {z_score:.2f}-sigma outlier (avg: ${avg_amount:.2f}, σ: ${std_dev:.2f})"
            else:
                reason = f"Amount ${current_amount:.2f} within normal range (z-score: {z_score:.2f})"
        except Exception:
            reason = "Could not calculate z-score from history"
    else:
        reason = f"Amount ${current_amount:.2f} is {multiplier:.1f}x average (insufficient history for z-score)"

    return RuleResult(
        name="amount_anomaly_check",
        triggered=triggered,
        reason=reason,
        weight=35 if triggered else 0,
    )

from datetime import datetime, timedelta
from app.rules.models import RuleResult


def check_velocity(transaction: dict, user_history: dict) -> RuleResult:
    """Check if user has too many transactions in a short time window.

    Rule: Flag if >5 transactions in the last 10 minutes (excluding current).
    Weight: 30 points if triggered.
    """
    recent_transactions = user_history.get("recent_transactions", [])

    if not recent_transactions:
        return RuleResult(
            name="velocity_check",
            triggered=False,
            reason="No recent transaction history",
            weight=0,
        )

    current_time = datetime.fromisoformat(transaction["timestamp"])
    window_start = current_time - timedelta(minutes=10)

    transactions_in_window = [
        t for t in recent_transactions
        if datetime.fromisoformat(t["timestamp"]) >= window_start
        and datetime.fromisoformat(t["timestamp"]) < current_time
    ]

    threshold = 5
    triggered = len(transactions_in_window) >= threshold

    reason = (
        f"User had {len(transactions_in_window)} transactions in last 10 minutes"
        if triggered
        else f"Only {len(transactions_in_window)} transactions in last 10 minutes (threshold: {threshold})"
    )

    return RuleResult(
        name="velocity_check",
        triggered=triggered,
        reason=reason,
        weight=30 if triggered else 0,
    )

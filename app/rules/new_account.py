from datetime import datetime, timedelta
from app.rules.models import RuleResult


def check_new_account_high_value(transaction: dict, user_history: dict) -> RuleResult:
    """Check if new account is making high-value transactions.

    Rule: Flag if account is <30 days old and transaction amount >$1000.
    Weight: 20 points if triggered.
    """
    account_creation_date = user_history.get("account_creation_date")

    if not account_creation_date:
        return RuleResult(
            name="new_account_high_value_check",
            triggered=False,
            reason="No account creation date data",
            weight=0,
        )

    account_age_days = 30
    threshold_amount = 1000.0

    if isinstance(account_creation_date, str):
        creation_dt = datetime.fromisoformat(account_creation_date)
    else:
        creation_dt = account_creation_date

    current_time = datetime.fromisoformat(transaction["timestamp"])
    account_age = current_time - creation_dt

    is_new_account = account_age < timedelta(days=account_age_days)
    amount = float(transaction["amount"])
    is_high_value = amount > threshold_amount

    triggered = is_new_account and is_high_value

    if triggered:
        reason = (
            f"New account ({account_age.days} days old) with high-value transaction "
            f"(${amount:.2f}, threshold: ${threshold_amount:.2f})"
        )
    elif is_new_account:
        reason = (
            f"New account ({account_age.days} days old) but transaction amount "
            f"(${amount:.2f}) is below threshold (${threshold_amount:.2f})"
        )
    else:
        reason = (
            f"Account age ({account_age.days} days) exceeds new account threshold "
            f"({account_age_days} days)"
        )

    return RuleResult(
        name="new_account_high_value_check",
        triggered=triggered,
        reason=reason,
        weight=20 if triggered else 0,
    )

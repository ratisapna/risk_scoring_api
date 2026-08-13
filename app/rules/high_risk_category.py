from app.rules.models import RuleResult

HIGH_RISK_CATEGORIES = {
    "gift_cards",
    "cryptocurrency_exchange",
    "wire_transfer",
    "money_remittance",
    "prepaid_cards",
    "gambling",
    "high_value_goods",
}


def check_high_risk_category(transaction: dict) -> RuleResult:
    """Check if merchant category is on the high-risk list.

    Rule: Flag if merchant_category matches known high-risk verticals.
    Weight: 25 points if triggered.
    """
    category = transaction.get("merchant_category", "").lower()

    triggered = category in HIGH_RISK_CATEGORIES

    reason = (
        f"Merchant category '{category}' is high-risk"
        if triggered
        else f"Merchant category '{category}' is acceptable"
    )

    return RuleResult(
        name="high_risk_category_check",
        triggered=triggered,
        reason=reason,
        weight=25 if triggered else 0,
    )

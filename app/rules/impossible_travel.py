from datetime import datetime
from geopy.distance import geodesic
from app.rules.models import RuleResult


def check_impossible_travel(transaction: dict, user_history: dict) -> RuleResult:
    """Check if transaction location is geographically implausible.

    Rule: Flag if distance / time implies impossible travel speed.
    Max feasible speed: ~900 km/h (commercial flight).
    Weight: 40 points if triggered.
    """
    last_location = user_history.get("last_transaction_location")
    last_time = user_history.get("last_transaction_time")

    if not last_location or not last_time:
        return RuleResult(
            name="impossible_travel_check",
            triggered=False,
            reason="No previous transaction location data",
            weight=0,
        )

    current_location = transaction.get("location")
    current_time = datetime.fromisoformat(transaction["timestamp"])

    if not current_location:
        return RuleResult(
            name="impossible_travel_check",
            triggered=False,
            reason="Current transaction has no location data",
            weight=0,
        )

    try:
        last_time_dt = (
            last_time if isinstance(last_time, datetime)
            else datetime.fromisoformat(last_time)
        )

        last_coords = tuple(map(float, last_location.split(",")))
        current_coords = tuple(map(float, current_location.split(",")))

        distance_km = geodesic(last_coords, current_coords).kilometers
        time_hours = (current_time - last_time_dt).total_seconds() / 3600

        if time_hours <= 0:
            return RuleResult(
                name="impossible_travel_check",
                triggered=False,
                reason="Transaction time before or same as previous (data issue)",
                weight=0,
            )

        required_speed_kmh = distance_km / time_hours
        max_feasible_speed = 900

        triggered = required_speed_kmh > max_feasible_speed
        reason = (
            f"Distance {distance_km:.0f} km in {time_hours:.2f} hours requires {required_speed_kmh:.0f} km/h"
            if triggered
            else f"Travel from {last_coords} to {current_coords} is feasible ({required_speed_kmh:.0f} km/h)"
        )

        return RuleResult(
            name="impossible_travel_check",
            triggered=triggered,
            reason=reason,
            weight=40 if triggered else 0,
        )
    except Exception as e:
        return RuleResult(
            name="impossible_travel_check",
            triggered=False,
            reason=f"Could not evaluate travel feasibility: {str(e)}",
            weight=0,
        )

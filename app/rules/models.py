from dataclasses import dataclass


@dataclass
class RuleResult:
    name: str
    triggered: bool
    reason: str
    weight: int


@dataclass
class ScoringResult:
    risk_score: int
    severity: str
    rules_triggered: list["RuleResult"]

    def to_dict(self):
        return {
            "risk_score": self.risk_score,
            "severity": self.severity,
            "rules_triggered": [
                {
                    "name": r.name,
                    "triggered": r.triggered,
                    "reason": r.reason,
                    "weight": r.weight,
                }
                for r in self.rules_triggered
            ],
        }

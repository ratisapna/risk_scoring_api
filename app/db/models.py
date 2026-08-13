from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Transaction(Base):
    """Transaction record with scoring result."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    merchant_category = Column(String, nullable=False)
    location = Column(String, nullable=False)  # lat,lon format

    # Scoring results
    risk_score = Column(Integer, nullable=False)
    severity = Column(String, nullable=False)  # low, medium, high
    rules_triggered = Column(JSON, nullable=False)  # List of triggered rules

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "merchant_category": self.merchant_category,
            "location": self.location,
            "risk_score": self.risk_score,
            "severity": self.severity,
            "rules_triggered": self.rules_triggered,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

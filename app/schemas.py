from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ScoringRequest(BaseModel):
    """Request schema for POST /score."""

    user_id: str = Field(..., min_length=1, max_length=255, description="User identifier")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    merchant_category: str = Field(..., min_length=1, description="Merchant category")
    location: str = Field(..., description="Location (lat,lon format)")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("timestamp must be ISO 8601 format")
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v):
        parts = v.split(",")
        if len(parts) != 2:
            raise ValueError("location must be in lat,lon format")
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError("invalid lat/lon coordinates")
        except ValueError:
            raise ValueError("location coordinates must be valid numbers")
        return v


class RuleTriggeredResponse(BaseModel):
    """Response schema for a single rule result."""

    name: str
    triggered: bool
    reason: str
    weight: int


class ScoringResponse(BaseModel):
    """Response schema for POST /score."""

    id: int
    risk_score: int = Field(..., ge=0, le=100)
    severity: str = Field(..., pattern="^(low|medium|high)$")
    rules_triggered: List[RuleTriggeredResponse]
    timestamp: str
    user_id: str
    amount: float
    merchant_category: str


class TransactionListResponse(BaseModel):
    """Response schema for GET /transactions."""

    id: int
    user_id: str
    amount: float
    timestamp: str
    merchant_category: str
    risk_score: int
    severity: str
    created_at: str


class TransactionDetailResponse(BaseModel):
    """Response schema for GET /transactions/{id}."""

    id: int
    user_id: str
    amount: float
    timestamp: str
    merchant_category: str
    location: str
    risk_score: int
    severity: str
    rules_triggered: List[RuleTriggeredResponse]
    created_at: str

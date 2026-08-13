from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import Transaction, APIKey, get_db
from app.rules import score_transaction
from app.schemas import (
    ScoringRequest,
    ScoringResponse,
    RuleTriggeredResponse,
    TransactionListResponse,
    TransactionDetailResponse,
)
from app.security import verify_api_key, check_rate_limit

router = APIRouter(prefix="/api/v1", tags=["transactions"])


@router.post(
    "/score",
    response_model=ScoringResponse,
    summary="Score a transaction",
    description="Evaluate a transaction through the rules engine and store the result",
)
async def score(
    request: ScoringRequest,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
):
    """Score a transaction and store the result."""
    check_rate_limit(db, api_key)
    try:
        # Prepare transaction dict for rules engine
        transaction_dict = {
            "user_id": request.user_id,
            "amount": request.amount,
            "timestamp": request.timestamp,
            "merchant_category": request.merchant_category,
            "location": request.location,
        }

        # Score the transaction (no user history yet)
        scoring_result = score_transaction(transaction_dict, user_history=None)

        # Store in database
        db_transaction = Transaction(
            user_id=request.user_id,
            amount=request.amount,
            timestamp=datetime.fromisoformat(request.timestamp),
            merchant_category=request.merchant_category,
            location=request.location,
            risk_score=scoring_result.risk_score,
            severity=scoring_result.severity,
            rules_triggered=[
                {
                    "name": rule.name,
                    "triggered": rule.triggered,
                    "reason": rule.reason,
                    "weight": rule.weight,
                }
                for rule in scoring_result.rules_triggered
            ],
        )
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)

        # Format response
        return ScoringResponse(
            id=db_transaction.id,
            risk_score=db_transaction.risk_score,
            severity=db_transaction.severity,
            rules_triggered=[
                RuleTriggeredResponse(**rule)
                for rule in db_transaction.rules_triggered
            ],
            timestamp=request.timestamp,
            user_id=request.user_id,
            amount=request.amount,
            merchant_category=request.merchant_category,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")


@router.get(
    "/transactions",
    response_model=list[TransactionListResponse],
    summary="List transactions",
    description="Retrieve stored transactions with optional filtering",
)
async def list_transactions(
    severity: Optional[str] = Query(
        None, description="Filter by severity (low, medium, high)"
    ),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
):
    """List transactions with optional filtering and pagination."""
    check_rate_limit(db, api_key)
    query = db.query(Transaction)

    # Apply filters
    if severity:
        if severity not in ["low", "medium", "high"]:
            raise HTTPException(status_code=400, detail="Invalid severity value")
        query = query.filter(Transaction.severity == severity)

    if user_id:
        query = query.filter(Transaction.user_id == user_id)

    # Order by created_at descending and apply pagination
    transactions = (
        query.order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return [
        TransactionListResponse(
            id=t.id,
            user_id=t.user_id,
            amount=t.amount,
            timestamp=t.timestamp.isoformat(),
            merchant_category=t.merchant_category,
            risk_score=t.risk_score,
            severity=t.severity,
            created_at=t.created_at.isoformat(),
        )
        for t in transactions
    ]


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionDetailResponse,
    summary="Get transaction details",
    description="Retrieve full details of a specific transaction",
)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
):
    """Get full details of a transaction including all rule results."""
    check_rate_limit(db, api_key)
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionDetailResponse(
        id=transaction.id,
        user_id=transaction.user_id,
        amount=transaction.amount,
        timestamp=transaction.timestamp.isoformat(),
        merchant_category=transaction.merchant_category,
        location=transaction.location,
        risk_score=transaction.risk_score,
        severity=transaction.severity,
        rules_triggered=[
            RuleTriggeredResponse(**rule)
            for rule in transaction.rules_triggered
        ],
        created_at=transaction.created_at.isoformat(),
    )


@router.post("/admin/create-key", tags=["admin"])
async def create_api_key(name: str = "test_key", key: Optional[str] = None, db: Session = Depends(get_db)):
    """TEMP: Create API key for testing. Remove after Phase 4 testing."""
    generated_key = key or APIKey.generate_key()
    if db.query(APIKey).filter(APIKey.key == generated_key).first():
        raise HTTPException(status_code=400, detail="Key already exists")
    api_key_obj = APIKey(name=name, key=generated_key, is_active=True)
    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)
    return {"id": api_key_obj.id, "key": api_key_obj.key, "name": api_key_obj.name}

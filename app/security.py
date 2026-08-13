from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from app.db import get_db, APIKey
from app.db.rate_limit import RateLimitLog


async def verify_api_key(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> APIKey:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API key")

    try:
        scheme, key = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    api_key = db.query(APIKey).filter(APIKey.key == key).first()
    if not api_key or not api_key.is_active:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    return api_key


def check_rate_limit(db: Session, api_key: APIKey, limit: int = 1000, hours: int = 1) -> None:
    count = RateLimitLog.count_recent_requests(db, api_key.id, hours)
    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} requests per {hours} hour(s)"
        )
    RateLimitLog.log_request(db, api_key.id)


def sanitize_merchant_category(category: str) -> str:
    allowed = {
        "grocery", "restaurant", "retail", "entertainment",
        "travel", "utilities", "health", "education",
        "cryptocurrency_exchange", "gambling", "wire_transfer",
        "money_remittance", "gift_cards", "prepaid_cards",
        "high_value_goods"
    }
    category_lower = category.lower().strip()
    if category_lower not in allowed:
        raise ValueError(f"Merchant category must be one of: {', '.join(sorted(allowed))}")
    return category_lower

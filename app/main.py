from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.db import Base, engine, get_db
from app.api import router
from app.db.api_key import APIKey
from app.db.rate_limit import RateLimitLog

settings = get_settings()

# Create database tables on startup
Base.metadata.create_all(bind=engine)

# Seed default API key for testing
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
try:
    if db.query(APIKey).filter(APIKey.key == "JzQEXbmTBMjDLxUNtHsO").first() is None:
        test_key = APIKey(name="test_key", key="JzQEXbmTBMjDLxUNtHsO", is_active=True)
        db.add(test_key)
        db.commit()
except Exception:
    db.rollback()
finally:
    db.close()

app = FastAPI(
    title="Transaction Risk Scoring API",
    description="Rule-based fraud detection and risk scoring for financial transactions",
    version="0.2.0",
    debug=settings.DEBUG,
)

# Include API routes
app.include_router(router)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint for deployment and monitoring.

    Returns:
        {"status": "healthy", "version": "0.2.0"}
    """
    return {
        "status": "healthy",
        "service": "transaction-risk-scoring-api",
        "version": "0.2.0",
    }

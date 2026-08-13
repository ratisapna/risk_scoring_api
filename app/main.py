from fastapi import FastAPI
from app.config import get_settings
from app.db import Base, engine
from app.api import router

settings = get_settings()

# Create database tables on startup
Base.metadata.create_all(bind=engine)

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

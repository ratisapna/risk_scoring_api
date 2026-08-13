from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Transaction Risk Scoring API",
    description="Rule-based fraud detection and risk scoring for financial transactions",
    version="0.1.0",
    debug=settings.DEBUG,
)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint for deployment and monitoring.

    Returns:
        {"status": "healthy", "version": "0.1.0"}
    """
    return {
        "status": "healthy",
        "service": "transaction-risk-scoring-api",
        "version": "0.1.0",
    }


# Placeholder routes (to be implemented in Phase 2)
@app.post("/score")
async def score_transaction():
    """Score a transaction through the rules engine. (Coming in Phase 2)"""
    return JSONResponse(
        status_code=501,
        content={"error": "Not yet implemented. Coming in Phase 2."}
    )


@app.get("/transactions")
async def get_transactions():
    """Retrieve scored transactions. (Coming in Phase 2)"""
    return JSONResponse(
        status_code=501,
        content={"error": "Not yet implemented. Coming in Phase 2."}
    )


@app.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Retrieve a single transaction by ID. (Coming in Phase 2)"""
    return JSONResponse(
        status_code=501,
        content={"error": "Not yet implemented. Coming in Phase 2."}
    )

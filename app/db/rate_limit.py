from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import Session
from app.db.models import Base


class RateLimitLog(Base):
    __tablename__ = "rate_limit_logs"

    id = Column(Integer, primary_key=True)
    api_key_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    @staticmethod
    def count_recent_requests(db: Session, api_key_id: int, hours: int = 1) -> int:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return db.query(func.count(RateLimitLog.id)).filter(
            RateLimitLog.api_key_id == api_key_id,
            RateLimitLog.timestamp >= cutoff
        ).scalar() or 0

    @staticmethod
    def log_request(db: Session, api_key_id: int) -> None:
        log = RateLimitLog(api_key_id=api_key_id)
        db.add(log)
        db.commit()

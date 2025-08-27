# =========================
# backend/domain/entities/idempotency.py
# =========================
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class IdempotencyRecord:
    key: str
    order_id: str
    signature_hash: str
    expires_at: datetime

    @staticmethod
    def ttl(hours: int = 48) -> datetime:
        return datetime.utcnow() + timedelta(hours=hours)

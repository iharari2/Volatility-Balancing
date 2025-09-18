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

    def __hash__(self):
        return hash((self.key, self.order_id, self.signature_hash))

    @staticmethod
    def ttl(hours: int = 48) -> datetime:
        return datetime.utcnow() + timedelta(hours=hours)

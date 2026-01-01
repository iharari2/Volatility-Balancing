# =========================
# backend/domain/entities/order.py
# =========================
from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, Any
from datetime import datetime, timezone
from domain.value_objects.types import OrderSide


@dataclass
class Order:
    id: str
    tenant_id: str
    portfolio_id: str
    position_id: str
    side: OrderSide
    qty: float
    status: Literal["submitted", "filled", "rejected"] = "submitted"
    idempotency_key: Optional[str] = None
    request_signature: Optional[Dict[str, Any]] = None
    # Commission fields (per spec)
    commission_rate_snapshot: Optional[float] = None  # Copied from config at order creation
    commission_estimated: Optional[float] = None  # Optional, for UI only
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __hash__(self):
        return hash((self.id, self.position_id, self.side, self.qty, self.status))

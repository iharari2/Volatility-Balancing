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
    position_id: str
    side: OrderSide
    qty: float
    status: Literal["submitted", "filled", "rejected"] = "submitted"
    idempotency_key: Optional[str] = None
    request_signature: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

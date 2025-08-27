# =========================
# backend/domain/entities/order.py
# =========================
from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, Any
from datetime import datetime

OrderSide = Literal["BUY", "SELL"]
OrderStatus = Literal["submitted", "accepted", "rejected", "filled", "canceled"]

@dataclass
class Order:
    id: str
    position_id: str
    side: OrderSide
    qty: float
    status: OrderStatus = "submitted"
    idempotency_key: Optional[str] = None
    request_signature: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

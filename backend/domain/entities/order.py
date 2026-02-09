# =========================
# backend/domain/entities/order.py
# =========================
from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, Any
from datetime import datetime, timezone
from domain.value_objects.types import OrderSide


# Extended status type to include broker workflow states
OrderStatus = Literal[
    "created",      # Initial state before submission
    "submitted",    # Submitted to our system
    "pending",      # Submitted to broker, awaiting acceptance
    "working",      # Accepted by broker, in the market
    "partial",      # Partially filled
    "filled",       # Completely filled
    "rejected",     # Rejected by broker or guardrails
    "cancelled",    # Cancelled by user or system
]


@dataclass
class Order:
    id: str
    tenant_id: str
    portfolio_id: str
    position_id: str
    side: OrderSide
    qty: float
    status: OrderStatus = "submitted"
    idempotency_key: Optional[str] = None
    request_signature: Optional[Dict[str, Any]] = None
    # Commission fields (per spec)
    commission_rate_snapshot: Optional[float] = None  # Copied from config at order creation
    commission_estimated: Optional[float] = None  # Optional, for UI only
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Broker integration fields (Phase 1)
    broker_order_id: Optional[str] = None  # Broker's order ID
    broker_status: Optional[str] = None  # Broker's status string
    submitted_to_broker_at: Optional[datetime] = None  # When submitted to broker
    filled_qty: float = 0.0  # Cumulative filled quantity
    avg_fill_price: Optional[float] = None  # Weighted average fill price
    total_commission: float = 0.0  # Cumulative commission paid
    last_broker_update: Optional[datetime] = None  # Last status update from broker
    rejection_reason: Optional[str] = None  # Reason for rejection (if rejected)
    time_in_force: str = "day"  # "day", "gtc", "ioc", "fok"

    def __hash__(self):
        return hash((self.id, self.position_id, self.side, self.qty, self.status))

# =========================
# backend/domain/entities/trade.py
# =========================
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from domain.value_objects.types import OrderSide


@dataclass
class Trade:
    id: str
    tenant_id: str
    portfolio_id: str
    order_id: str
    position_id: str
    side: OrderSide
    qty: float
    price: float
    commission: float
    commission_rate_effective: Optional[float] = (
        None  # Actual rate applied by broker (may differ from order snapshot)
    )
    status: str = "executed"  # executed, partially_executed, cancelled, expired
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __hash__(self):
        return hash((self.id, self.order_id, self.position_id, self.side, self.qty, self.price))

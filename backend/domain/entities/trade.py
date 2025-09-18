# =========================
# backend/domain/entities/trade.py
# =========================
from dataclasses import dataclass
from datetime import datetime
from domain.value_objects.types import OrderSide


@dataclass
class Trade:
    id: str
    order_id: str
    position_id: str
    side: OrderSide
    qty: float
    price: float
    commission: float
    executed_at: datetime

    def __hash__(self):
        return hash((self.id, self.order_id, self.position_id, self.side, self.qty, self.price))

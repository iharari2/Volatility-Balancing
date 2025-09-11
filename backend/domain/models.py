from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    SUBMITTED = "submitted"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELED = "canceled"


@dataclass
class Position:
    id: str
    symbol: str
    asset_qty: float
    cash: float
    min_alloc: float
    max_alloc: float
    last_price: float = 0.0

    def nav(self) -> float:
        return self.cash + self.asset_qty * self.last_price


@dataclass
class Order:
    id: str
    position_id: str
    side: Side
    qty: float
    created_at: datetime
    idempotency_key: Optional[str] = None
    status: OrderStatus = OrderStatus.SUBMITTED


@dataclass
class Trade:
    id: str
    order_id: str
    position_id: str
    side: Side
    qty: float
    price: float
    commission: float
    executed_at: datetime


@dataclass
class Event:
    id: str
    position_id: str
    type: str
    ts: datetime
    payload: Dict[str, Any]


def clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def pct(amount: float, total: float) -> float:
    if total == 0:
        return 0.0
    # ensure float, not Any
    val: float = amount / total
    return val

# =========================
# backend/domain/ports/orders_repo.py
# =========================
from typing import Protocol, Optional
from datetime import date

from domain.entities.order import Order


class OrdersRepo(Protocol):
    def get(self, order_id: str) -> Optional[Order]: ...
    def save(self, order: Order) -> None: ...
    def count_for_position_on_day(self, position_id: str, day: date) -> int: ...
    def clear(self) -> None: ...
# =========================
# backend/infrastructure/persistence/memory/orders_repo_mem.py
# =========================
from collections import defaultdict
from datetime import date
from typing import Dict, Optional

from domain.entities.order import Order
from domain.ports.orders_repo import OrdersRepo

class InMemoryOrdersRepo(OrdersRepo):
    def __init__(self) -> None:
        self._items: Dict[str, Order] = {}
        self._count_index: Dict[tuple[str, date], int] = defaultdict(int)

    def get(self, order_id: str) -> Optional[Order]:
        return self._items.get(order_id)

    def save(self, order: Order) -> None:
        self._items[order.id] = order
        self._count_index[(order.position_id, order.created_at.date())] += 1

    def count_for_position_on_day(self, position_id: str, day: date) -> int:
        return self._count_index[(position_id, day)]

    def clear(self) -> None:
        self._items.clear()
        self._count_index.clear()

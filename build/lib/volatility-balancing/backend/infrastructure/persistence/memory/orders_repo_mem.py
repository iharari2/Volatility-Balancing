# =========================
# backend/infrastructure/persistence/memory/orders_repo_mem.py
# =========================
from collections import defaultdict
from datetime import date
from typing import Dict, Optional, Iterable

from domain.entities.order import Order
from domain.ports.orders_repo import OrdersRepo


class InMemoryOrdersRepo(OrdersRepo):
    def __init__(self) -> None:
        self._items: Dict[str, Order] = {}
        self._count_index: Dict[tuple[str, date], int] = defaultdict(int)
        self._by_position: Dict[str, list[str]] = defaultdict(list)  # NEW

    def get(self, order_id: str) -> Optional[Order]:
        return self._items.get(order_id)

    def save(self, order: Order) -> None:
        is_new = order.id not in self._items
        self._items[order.id] = order
        if is_new:
            self._count_index[(order.position_id, order.created_at.date())] += 1
            self._by_position[order.position_id].append(order.id)  # NEW

    def count_for_position_on_day(self, position_id: str, day: date) -> int:
        return self._count_index[(position_id, day)]

    def list_for_position(self, position_id: str, limit: int = 100) -> Iterable[Order]:  # NEW
        ids = self._by_position.get(position_id, [])
        # newest first (we rely on created_at order of inserts)
        return list(reversed([self._items[i] for i in ids]))[:limit]

    def clear(self) -> None:
        self._items.clear()
        self._count_index.clear()
        self._by_position.clear()  # NEW

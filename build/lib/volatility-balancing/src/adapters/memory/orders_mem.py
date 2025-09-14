from typing import Dict, Optional
from app.domain.models import Order

class InMemoryOrderRepo:
    def __init__(self):
        self._data: Dict[str, Order] = {}
        self._by_key: Dict[str, str] = {}

    def get(self, order_id: str) -> Optional[Order]:
        return self._data.get(order_id)

    def save(self, order: Order) -> None:
        self._data[order.id] = order
        if order.idempotency_key:
            self._by_key[order.idempotency_key] = order.id

    def find_by_idempotency(self, key: str) -> Optional[Order]:
        oid = self._by_key.get(key)
        return self._data.get(oid) if oid else None
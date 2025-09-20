# =========================
# backend/infrastructure/persistence/memory/positions_repo_mem.py
# =========================
import uuid
from typing import Dict, Optional

from domain.entities.position import Position
from domain.ports.positions_repo import PositionsRepo


class InMemoryPositionsRepo(PositionsRepo):
    def __init__(self) -> None:
        self._items: Dict[str, Position] = {}

    def get(self, position_id: str) -> Optional[Position]:
        return self._items.get(position_id)

    def create(
        self, ticker: str, qty: float, cash: float, anchor_price: Optional[float] = None
    ) -> Position:
        pid = f"pos_{uuid.uuid4().hex[:8]}"
        pos = Position(id=pid, ticker=ticker, qty=qty, cash=cash, anchor_price=anchor_price)
        self._items[pid] = pos
        return pos

    def save(self, position: Position) -> None:
        print(f"DEBUG: Saving position {position.id} with anchor_price={position.anchor_price}")
        self._items[position.id] = position
        print(
            f"DEBUG: Saved position {position.id}, stored anchor_price={self._items[position.id].anchor_price}"
        )

    def clear(self) -> None:
        self._items.clear()

    def list_all(self) -> list[Position]:
        return list(self._items.values())

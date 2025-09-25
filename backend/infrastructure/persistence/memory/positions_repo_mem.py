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

    def delete(self, position_id: str) -> bool:
        """Delete a position by ID. Returns True if deleted, False if not found."""
        if position_id in self._items:
            del self._items[position_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all positions."""
        self._items.clear()

    def list_all(self) -> list[Position]:
        """List all positions."""
        return list(self._items.values())

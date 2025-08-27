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

    def create(self, ticker: str, qty: float, cash: float) -> Position:
        pid = f"pos_{uuid.uuid4().hex[:8]}"
        pos = Position(id=pid, ticker=ticker, qty=qty, cash=cash)
        self._items[pid] = pos
        return pos

    def save(self, position: Position) -> None:
        self._items[position.id] = position

    def clear(self) -> None:
        self._items.clear()


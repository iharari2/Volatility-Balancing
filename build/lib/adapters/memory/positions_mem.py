from typing import Dict, Optional
from app.domain.models import Position

class InMemoryPositionRepo:
    def __init__(self):
        self._data: Dict[str, Position] = {}

    def get(self, position_id: str) -> Optional[Position]:
        return self._data.get(position_id)

    def save(self, pos: Position) -> None:
        self._data[pos.id] = pos
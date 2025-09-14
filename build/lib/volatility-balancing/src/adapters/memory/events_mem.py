from typing import Dict, List, Iterable
from app.domain.models import Event

class InMemoryEventRepo:
    def __init__(self):
        self._list: List[Event] = []

    def append(self, evt: Event) -> None:
        self._list.append(evt)

    def list_for_position(self, position_id: str) -> Iterable[Event]:
        return [e for e in self._list if e.position_id == position_id]
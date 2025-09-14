# =========================
# backend/infrastructure/persistence/memory/events_repo_mem.py
# =========================
from typing import Dict, List, Iterable
from domain.entities.event import Event
from domain.ports.events_repo import EventsRepo

class InMemoryEventsRepo(EventsRepo):
    def __init__(self) -> None:
        self._items: Dict[str, List[Event]] = {}

    def append(self, event: Event) -> None:
        self._items.setdefault(event.position_id, []).append(event)

    def list_for_position(self, position_id: str, limit: int = 100) -> Iterable[Event]:
        return list(self._items.get(position_id, []))[-limit:]

    def clear(self) -> None:
        self._items.clear()

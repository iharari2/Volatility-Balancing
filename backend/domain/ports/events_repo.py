# =========================
# backend/domain/ports/events_repo.py
# =========================

from typing import Protocol, Iterable
from domain.entities.event import Event

class EventsRepo(Protocol):
    def append(self, event: Event) -> None: ...
    def list_for_position(self, position_id: str, limit: int = 100) -> Iterable[Event]: ...
    def clear(self) -> None: ...

# =========================
# backend/infrastructure/adapters/event_logger_adapter.py
# =========================
"""Adapter implementing IEventLogger using existing EventsRepo."""

from application.ports.repos import IEventLogger
from domain.ports.events_repo import EventsRepo
from domain.entities.event import Event
from infrastructure.time.clock import Clock
from uuid import uuid4


class EventLoggerAdapter(IEventLogger):
    """Adapter that implements IEventLogger using existing EventsRepo."""

    def __init__(self, events_repo: EventsRepo, clock: Clock):
        """
        Initialize adapter with existing events repository.

        Args:
            events_repo: Existing EventsRepo implementation
            clock: Clock service for timestamps
        """
        self.events_repo = events_repo
        self.clock = clock

    def log_event(self, event_type: str, payload: dict) -> None:
        """Log an event with type and payload."""
        # Extract position_id from payload if available
        position_id = payload.get("position_id", "system")

        # Create Event entity
        event = Event(
            id=f"evt_{uuid4().hex[:8]}",
            position_id=position_id,
            type=event_type,
            inputs=payload,  # Store full payload as inputs
            outputs={},  # No outputs for now
            message=payload.get("reason") or payload.get("message") or event_type,
            ts=self.clock.now(),
        )

        # Save to repository
        self.events_repo.append(event)

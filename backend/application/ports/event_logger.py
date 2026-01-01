# =========================
# backend/application/ports/event_logger.py
# =========================
"""Port interface for event logging."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable
from application.events import EventRecord, EventType


class IEventLogger(ABC):
    """Port for unified event logging with trace_id support."""

    @abstractmethod
    def log_event(self, event: EventRecord) -> None:
        """Log an event record."""
        raise NotImplementedError

    def log(
        self,
        event_type: EventType,
        *,
        tenant_id=None,
        portfolio_id=None,
        asset_id=None,
        trace_id=None,
        parent_event_id=None,
        source=None,
        payload=None,
        version=1,
    ) -> EventRecord:
        """Convenience method to create and log an event."""
        event = EventRecord.new(
            event_type=event_type,
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            trace_id=trace_id,
            parent_event_id=parent_event_id,
            source=source,
            payload=payload,
            version=version,
        )
        self.log_event(event)
        return event

    def log_batch(self, events: Iterable[EventRecord]) -> None:
        """Log multiple events in a batch."""
        for e in events:
            self.log_event(e)

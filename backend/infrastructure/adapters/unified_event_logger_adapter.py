# =========================
# backend/infrastructure/adapters/unified_event_logger_adapter.py
# =========================
"""Adapter that bridges old IEventLogger interface to new unified EventRecord system."""

from typing import Optional
from application.ports.event_logger import IEventLogger as NewIEventLogger
from application.events import EventRecord, EventType
from application.ports.repos import IEventLogger as OldIEventLogger


class UnifiedEventLoggerAdapter(OldIEventLogger):
    """
    Adapter that implements the old IEventLogger interface using the new unified EventRecord system.

    This allows existing code to continue using the old interface while new code uses EventRecord.
    """

    def __init__(self, new_logger: NewIEventLogger):
        """
        Initialize adapter with new unified event logger.

        Args:
            new_logger: New IEventLogger implementation that uses EventRecord
        """
        self.new_logger = new_logger
        self._current_trace_id: Optional[str] = None
        self._last_event_id: Optional[str] = None

    def log_event(self, event_type: str, payload: dict) -> None:
        """
        Log an event using the old interface, converting to new EventRecord format.

        Args:
            event_type: Event type string (will be mapped to EventType enum)
            payload: Event payload dictionary
        """
        # Map old event type strings to new EventType enum
        event_type_map = {
            "price_event": EventType.PRICE_EVENT,
            "trigger_evaluated": EventType.TRIGGER_EVALUATED,
            "guardrail_evaluated": EventType.GUARDRAIL_EVALUATED,
            "order_created": EventType.ORDER_CREATED,
            "live_order_submitted": EventType.ORDER_CREATED,
            "execution_recorded": EventType.EXECUTION_RECORDED,
            "position_updated": EventType.POSITION_UPDATED,
            "dividend_paid": EventType.DIVIDEND_PAID,
        }

        # Get EventType or default to a generic type
        mapped_type = event_type_map.get(event_type.lower(), EventType.VIEW_RENDERED)

        # Extract metadata from payload
        tenant_id = payload.get("tenant_id")
        portfolio_id = payload.get("portfolio_id")
        asset_id = payload.get("asset_id") or payload.get("ticker")
        position_id = payload.get("position_id")

        # Use existing trace_id or create new one
        trace_id = payload.get("trace_id") or self._current_trace_id

        # Create event record
        event = EventRecord.new(
            event_type=mapped_type,
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            trace_id=trace_id,
            parent_event_id=self._last_event_id,
            source="orchestrator" if "position_id" in payload else "system",
            payload=payload,
        )

        # Log using new interface
        self.new_logger.log_event(event)

        # Update state for next event
        self._last_event_id = event.event_id
        if trace_id:
            self._current_trace_id = trace_id

    def set_trace_id(self, trace_id: str) -> None:
        """Set the current trace_id for subsequent events."""
        self._current_trace_id = trace_id

    def reset_trace(self) -> None:
        """Reset trace tracking (start new trace)."""
        self._current_trace_id = None
        self._last_event_id = None

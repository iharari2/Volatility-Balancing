# =========================
# backend/application/events.py
# =========================
"""Unified event model for audit trail logging."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class EventType(str, Enum):
    """Event types for audit trail logging."""

    PRICE_EVENT = "PriceEvent"
    TRIGGER_EVALUATED = "TriggerEvaluated"
    GUARDRAIL_EVALUATED = "GuardrailEvaluated"
    ORDER_CREATED = "OrderCreated"
    EXECUTION_RECORDED = "ExecutionRecorded"
    POSITION_UPDATED = "PositionUpdated"
    DIVIDEND_PAID = "DividendPaid"
    VIEW_RENDERED = "ViewRendered"


@dataclass
class EventRecord:
    """Unified event record for audit trail."""

    event_id: str
    event_type: EventType
    created_at: datetime
    tenant_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    asset_id: Optional[str] = None
    trace_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    source: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    version: int = 1

    @staticmethod
    def new(
        event_type: EventType,
        tenant_id: Optional[str] = None,
        portfolio_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
        source: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        version: int = 1,
    ) -> "EventRecord":
        """Create a new event record."""
        return EventRecord(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            created_at=datetime.now(timezone.utc),
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            trace_id=trace_id or str(uuid.uuid4()),
            parent_event_id=parent_event_id,
            source=source,
            payload=payload or {},
            version=version,
        )

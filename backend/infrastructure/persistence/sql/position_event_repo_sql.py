# =========================
# backend/infrastructure/persistence/sql/position_event_repo_sql.py
# =========================
"""SQL implementation of PositionEventRepo."""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, desc

from domain.ports.position_event_repo import PositionEventRepo
from infrastructure.persistence.sql.models import PositionEventModel


class PositionEventRepoSQL(PositionEventRepo):
    """SQL implementation of PositionEventRepo."""

    def __init__(self, session_factory):
        """
        Initialize SQL repository.

        Args:
            session_factory: Callable that returns a SQLAlchemy Session
        """
        self.session_factory = session_factory

    def save(self, event_data: Dict[str, Any]) -> str:
        """Save a position event record (immutable log)."""
        with self.session_factory() as session:
            # Generate ID if not provided
            event_id = event_data.get("event_id") or f"event_{uuid4().hex[:16]}"

            # Ensure action is one of the allowed values (BUY, SELL, NONE)
            # Map HOLD and SKIP to NONE to comply with database constraint
            # This is a safety check - build_position_event_from_timeline should already map it
            action = event_data.get("action", "NONE")
            if action not in ("BUY", "SELL", "NONE"):
                action = "NONE"
            # Always update event_data with the mapped action to ensure consistency
            event_data = {**event_data, "action": action}

            # Create new record (events are immutable, no updates)
            record = PositionEventModel(
                event_id=event_id, **{k: v for k, v in event_data.items() if k != "event_id"}
            )
            session.add(record)
            session.commit()
            return record.event_id  # PositionEventModel uses event_id, not id

    def get_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get an event record by ID."""
        with self.session_factory() as session:
            record = session.get(PositionEventModel, event_id)
            if not record:
                return None
            return self._model_to_dict(record)

    def list_by_position(
        self,
        position_id: str,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List event records for a position."""
        with self.session_factory() as session:
            query = select(PositionEventModel).where(PositionEventModel.position_id == position_id)

            if event_type:
                query = query.where(PositionEventModel.event_type == event_type)

            if start_date:
                query = query.where(PositionEventModel.timestamp >= start_date)

            if end_date:
                query = query.where(PositionEventModel.timestamp <= end_date)

            query = query.order_by(desc(PositionEventModel.timestamp))

            if limit:
                query = query.limit(limit)

            records = session.execute(query).scalars().all()
            return [self._model_to_dict(r) for r in records]

    def _model_to_dict(self, record: PositionEventModel) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        result = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name, None)
            # Convert datetime to ISO string for JSON serialization
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            result[column.name] = value
        return result

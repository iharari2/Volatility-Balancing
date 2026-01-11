from __future__ import annotations

from typing import Iterable, Any
from decimal import Decimal

from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session, sessionmaker

from domain.entities.event import Event
from domain.ports.events_repo import EventsRepo
from .models import EventModel

__all__ = ["SQLEventsRepo"]


def _make_json_serializable(obj: Any) -> Any:
    """
    Recursively convert Decimal values to float for JSON serialization.

    Args:
        obj: Object that may contain Decimal values

    Returns:
        Object with all Decimal values converted to float
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_serializable(item) for item in obj]
    else:
        return obj


class SQLEventsRepo(EventsRepo):
    """
    SQL-backed EventsRepo implementation.

    IMPORTANT:
    ----------
    The physical `events` table in existing deployments may not have all the
    columns defined on `EventModel` (e.g. missing `trace_id`, `tenant_id`,
    `portfolio_id`, `event_type`, etc.).

    Using `EventModel` directly for INSERTs would therefore generate SQL that
    references non-existent columns, causing OperationalError like:

        sqlite3.OperationalError: table events has no column named trace_id

    To make this repository resilient to partial / legacy schemas, we REFLECT
    the actual `events` table from the database and build INSERT statements
    only with the columns that physically exist there.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory
        # Lazily-reflected events table (actual DB schema, not ORM model)
        self._reflected_events_table: Table | None = None

    def _get_events_table(self, session: Session) -> Table | None:
        """
        Reflect the real `events` table from the database.

        This ignores the ORM EventModel definition and ensures we only ever
        reference columns that actually exist in the underlying table.
        """
        if self._reflected_events_table is not None:
            return self._reflected_events_table

        try:
            metadata = MetaData()
            bind = session.get_bind()
            self._reflected_events_table = Table("events", metadata, autoload_with=bind)
            return self._reflected_events_table
        except Exception as e:
            # If reflection fails, log and disable event persistence rather than crashing
            print(f"⚠️  SQLEventsRepo: failed to reflect 'events' table: {e}")
            self._reflected_events_table = None
            return None

    def append(self, event: Event) -> None:
        with self._sf() as s:
            events_table = self._get_events_table(s)
            if events_table is None:
                # Nothing we can safely do without a reflected table
                print("⚠️  SQLEventsRepo.append: 'events' table unavailable, skipping event write")
                return

            # Use the REAL physical columns from the reflected table
            table_columns = {col.name for col in events_table.columns}

            # Map domain Event fields into a generic event_data dict.
            # We deliberately do NOT include newer metadata fields (tenant_id, trace_id, etc.)
            # because older schemas won't have them. If newer deployments add those columns,
            # they simply won't get values from this legacy write path.
            # Convert Decimal values to float for JSON serialization
            event_data = {
                "id": event.id,
                "position_id": event.position_id,
                "type": event.type,
                "event_type": event.type,
                "inputs": _make_json_serializable(event.inputs),
                "outputs": _make_json_serializable(event.outputs),
                "message": event.message,
                # Prefer `timestamp`/`ts` compatibility if present in table
                "ts": event.ts,
                "timestamp": event.ts,
            }

            # Filter to only include columns that physically exist in the DB table
            filtered_data = {k: v for k, v in event_data.items() if k in table_columns}

            if not filtered_data:
                # If nothing matches, don't attempt an insert
                print(
                    "⚠️  SQLEventsRepo.append: no matching columns between event data and "
                    "'events' table schema; skipping event write"
                )
                return

            try:
                insert_stmt = events_table.insert().values(**filtered_data)
                s.execute(insert_stmt)
                s.commit()
            except Exception as e:
                # Do not let event logging break trading/tick flows
                s.rollback()
                print(f"⚠️  SQLEventsRepo.append: failed to write event: {e}")

    def list_for_position(self, position_id: str, limit: int = 100) -> Iterable[Event]:
        with self._sf() as s:
            stmt = (
                select(EventModel)
                .where(EventModel.position_id == position_id)
                .order_by(EventModel.ts.desc())
                .limit(limit)
            )
            rows: list[EventModel] = list(s.execute(stmt).scalars().all())
            return [
                Event(
                    id=r.id,
                    position_id=r.position_id,
                    type=r.type,
                    inputs=r.inputs or {},
                    outputs=r.outputs or {},
                    message=r.message,
                    ts=r.ts,
                )
                for r in rows
            ]

    def clear(self) -> None:
        with self._sf() as s:
            s.query(EventModel).delete()
            s.commit()

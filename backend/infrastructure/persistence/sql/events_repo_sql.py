from __future__ import annotations
from typing import Iterable
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from domain.entities.event import Event
from domain.ports.events_repo import EventsRepo
from .models import EventModel

__all__ = ["SQLEventsRepo"]  # <- explicit export


class SQLEventsRepo(EventsRepo):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def append(self, event: Event) -> None:
        with self._sf() as s:
            s.add(
                EventModel(
                    id=event.id,
                    position_id=event.position_id,
                    type=event.type,
                    inputs=event.inputs,
                    outputs=event.outputs,
                    message=event.message,
                    ts=event.ts,
                )
            )
            s.commit()

    def list_for_position(self, position_id: str, limit: int = 100) -> Iterable[Event]:
        with self._sf() as s:
            stmt = (
                select(EventModel)
                .where(EventModel.position_id == position_id)
                .order_by(EventModel.ts.desc())
                .limit(limit)
            )
            rows = s.execute(stmt).scalars().all()
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

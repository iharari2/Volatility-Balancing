# =========================
# backend/infrastructure/persistence/sql/positions_repo_sql.py
# =========================
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import sessionmaker

from domain.entities.position import Position
from domain.ports.positions_repo import PositionsRepo
from .models import PositionModel

__all__ = ["SQLPositionsRepo"]  # <- explicit export


class SQLPositionsRepo(PositionsRepo):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def get(self, position_id: str) -> Optional[Position]:
        with self._sf() as s:
            row = s.get(PositionModel, position_id)
            if not row:
                return None
            return Position(
                id=row.id,
                ticker=row.ticker,
                qty=row.qty,
                cash=row.cash,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    def create(self, ticker: str, qty: float, cash: float) -> Position:
        import uuid

        with self._sf() as s:
            pid = f"pos_{uuid.uuid4().hex[:8]}"
            row = PositionModel(id=pid, ticker=ticker, qty=qty, cash=cash)
            s.add(row)
            s.commit()
            return Position(
                id=row.id,
                ticker=row.ticker,
                qty=row.qty,
                cash=row.cash,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    def save(self, position: Position) -> None:
        with self._sf() as s:
            row = s.get(PositionModel, position.id)
            if row is None:
                s.add(
                    PositionModel(
                        id=position.id,
                        ticker=position.ticker,
                        qty=position.qty,
                        cash=position.cash,
                        created_at=position.created_at,
                        updated_at=position.updated_at,
                    )
                )
            else:
                row.ticker = position.ticker
                row.qty = position.qty
                row.cash = position.cash
                row.updated_at = position.updated_at
            s.commit()

    def clear(self) -> None:
        with self._sf() as s:
            s.query(PositionModel).delete()
            s.commit()

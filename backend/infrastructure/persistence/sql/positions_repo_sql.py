from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from domain.entities.position import Position
from domain.ports.positions_repo import PositionsRepo
from domain.value_objects.order_policy import OrderPolicy
from .models import PositionModel


def _to_entity(m: PositionModel) -> Position:
    """SQL row -> domain entity."""
    return Position(
        id=m.id,
        ticker=m.ticker,
        qty=m.qty,
        cash=m.cash,
        created_at=m.created_at,
        updated_at=m.updated_at,
        # Coalesce nullable policy columns to defaults
        order_policy=OrderPolicy(
            min_qty=m.op_min_qty or 0.0,
            min_notional=m.op_min_notional or 0.0,
            lot_size=m.op_lot_size or 0.0,
            qty_step=m.op_qty_step or 0.0,
            action_below_min=m.op_action_below_min or "hold",
        ),
        # guardrails remain whatever the entity default is (not persisted yet)
    )


def _new_row_from_entity(p: Position) -> PositionModel:
    """Domain entity -> new SQL row (insert)."""
    return PositionModel(
        id=p.id,
        ticker=p.ticker,
        qty=p.qty,
        cash=p.cash,
        created_at=p.created_at,
        updated_at=p.updated_at,
        op_min_qty=p.order_policy.min_qty,
        op_min_notional=p.order_policy.min_notional,
        op_lot_size=p.order_policy.lot_size,
        op_qty_step=p.order_policy.qty_step,
        op_action_below_min=p.order_policy.action_below_min,
    )


def _apply_entity_to_row(row: PositionModel, p: Position) -> None:
    """Apply domain entity fields onto an existing SQL row (update)."""
    row.ticker = p.ticker
    row.qty = p.qty
    row.cash = p.cash
    row.updated_at = p.updated_at

    row.op_min_qty = p.order_policy.min_qty
    row.op_min_notional = p.order_policy.min_notional
    row.op_lot_size = p.order_policy.lot_size
    row.op_qty_step = p.order_policy.qty_step
    row.op_action_below_min = p.order_policy.action_below_min


class SQLPositionsRepo(PositionsRepo):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    # --- Reads ---

    def get(self, position_id: str) -> Optional[Position]:
        with self._sf() as s:
            row = s.get(PositionModel, position_id)
            if not row:
                return None
            return _to_entity(row)

    def list(self, limit: int = 100, offset: int = 0) -> List[Position]:
        with self._sf() as s:
            rows = (
                s.query(PositionModel)
                .order_by(PositionModel.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [_to_entity(r) for r in rows]

    # --- Writes ---

    def save(self, position: Position) -> None:
        with self._sf() as s:
            row = s.get(PositionModel, position.id)
            if row is None:
                s.add(_new_row_from_entity(position))
            else:
                _apply_entity_to_row(row, position)
            s.commit()

    def create(
        self,
        ticker: str,
        qty: float,
        cash: float,
        order_policy: Optional[OrderPolicy] = None,
    ) -> Position:
        """Create + persist a new Position (id + timestamps set here)."""
        now = datetime.now(timezone.utc)
        pos = Position(
            id=f"pos_{uuid4().hex[:8]}",
            ticker=ticker,
            qty=qty,
            cash=cash,
            created_at=now,
            updated_at=now,
            order_policy=order_policy or OrderPolicy(),
        )
        self.save(pos)
        return pos

    def clear(self) -> None:
        """Wipe all positions (test helper / dev)."""
        with self._sf() as s:
            s.query(PositionModel).delete()
            s.commit()

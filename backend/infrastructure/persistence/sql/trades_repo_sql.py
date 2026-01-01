# =========================
# backend/infrastructure/persistence/sql/trades_repo_sql.py
# =========================
from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session, sessionmaker

from domain.entities.trade import Trade
from domain.ports.trades_repo import TradesRepo
from infrastructure.persistence.sql.models import TradeModel


def _to_entity(row: TradeModel) -> Trade:
    """Convert SQLAlchemy row to domain entity."""

    return Trade(
        id=row.id,
        tenant_id=row.tenant_id,
        portfolio_id=row.portfolio_id,
        order_id=row.order_id,
        position_id=row.position_id,
        side=row.side,  # type: OrderSide
        qty=row.qty,
        price=row.price,
        commission=row.commission,
        commission_rate_effective=getattr(row, "commission_rate_effective", None),
        status=getattr(row, "status", "executed"),
        executed_at=row.executed_at,
    )


def _new_row_from_entity(trade: Trade) -> TradeModel:
    """Create new SQLAlchemy row from domain entity."""
    return TradeModel(
        id=trade.id,
        tenant_id=trade.tenant_id,
        portfolio_id=trade.portfolio_id,
        order_id=trade.order_id,
        position_id=trade.position_id,
        side=trade.side,
        qty=trade.qty,
        price=trade.price,
        commission=trade.commission,
        commission_rate_effective=trade.commission_rate_effective,
        status=trade.status,
        executed_at=trade.executed_at,
    )


class SQLTradesRepo(TradesRepo):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def save(self, trade: Trade) -> None:
        """Save a trade to SQL storage."""
        with self._sf() as s:
            row = s.get(TradeModel, trade.id)
            if row is None:
                s.add(_new_row_from_entity(trade))
            else:
                # Update existing trade (shouldn't happen in practice)
                row.tenant_id = trade.tenant_id
                row.portfolio_id = trade.portfolio_id
                row.order_id = trade.order_id
                row.position_id = trade.position_id
                row.side = trade.side.value
                row.qty = trade.qty
                row.price = trade.price
                row.commission = trade.commission
                row.commission_rate_effective = trade.commission_rate_effective
                row.status = trade.status
                row.executed_at = trade.executed_at
            s.commit()

    def get(self, trade_id: str) -> Optional[Trade]:
        """Get a trade by ID."""
        with self._sf() as s:
            row = s.get(TradeModel, trade_id)
            if not row:
                return None
            return _to_entity(row)

    def list_for_position(self, position_id: str, limit: int = 100) -> List[Trade]:
        """List trades for a position, ordered by execution time (newest first)."""
        with self._sf() as s:
            rows = (
                s.query(TradeModel)
                .filter(TradeModel.position_id == position_id)
                .order_by(TradeModel.executed_at.desc())
                .limit(limit)
                .all()
            )
            return [_to_entity(r) for r in rows]

    def list_for_order(self, order_id: str) -> List[Trade]:
        """List trades for an order (typically 1 trade per order)."""
        with self._sf() as s:
            rows = (
                s.query(TradeModel)
                .filter(TradeModel.order_id == order_id)
                .order_by(TradeModel.executed_at.desc())
                .all()
            )
            return [_to_entity(r) for r in rows]

    def clear(self) -> None:
        """Clear all trades (test helper)."""
        with self._sf() as s:
            s.query(TradeModel).delete()
            s.commit()

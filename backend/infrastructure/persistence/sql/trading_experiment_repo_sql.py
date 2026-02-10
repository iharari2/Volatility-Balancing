# backend/infrastructure/persistence/sql/trading_experiment_repo_sql.py
from __future__ import annotations

from typing import Optional, List

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import select

from domain.entities.trading_experiment import TradingExperiment
from domain.ports.trading_experiment_repo import TradingExperimentRepo
from .models import TradingExperimentModel


def _to_entity(m: TradingExperimentModel) -> TradingExperiment:
    """SQL row -> domain entity."""
    return TradingExperiment(
        id=m.id,
        tenant_id=m.tenant_id,
        name=m.name,
        ticker=m.ticker,
        initial_capital=m.initial_capital,
        status=m.status,
        started_at=m.started_at,
        ended_at=m.ended_at,
        position_id=m.position_id,
        portfolio_id=m.portfolio_id,
        baseline_price=m.baseline_price,
        baseline_shares_equivalent=m.baseline_shares_equivalent,
        current_portfolio_value=m.current_portfolio_value,
        current_buyhold_value=m.current_buyhold_value,
        evaluation_count=m.evaluation_count,
        trade_count=m.trade_count,
        total_commission_paid=m.total_commission_paid,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _new_row_from_entity(e: TradingExperiment) -> TradingExperimentModel:
    """Domain entity -> new SQL row (insert)."""
    return TradingExperimentModel(
        id=e.id,
        tenant_id=e.tenant_id,
        name=e.name,
        ticker=e.ticker,
        initial_capital=e.initial_capital,
        status=e.status,
        started_at=e.started_at,
        ended_at=e.ended_at,
        position_id=e.position_id,
        portfolio_id=e.portfolio_id,
        baseline_price=e.baseline_price,
        baseline_shares_equivalent=e.baseline_shares_equivalent,
        current_portfolio_value=e.current_portfolio_value,
        current_buyhold_value=e.current_buyhold_value,
        evaluation_count=e.evaluation_count,
        trade_count=e.trade_count,
        total_commission_paid=e.total_commission_paid,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


def _apply_entity_to_row(row: TradingExperimentModel, e: TradingExperiment) -> None:
    """Apply domain entity fields onto an existing SQL row (update)."""
    row.name = e.name
    row.ticker = e.ticker
    row.initial_capital = e.initial_capital
    row.status = e.status
    row.started_at = e.started_at
    row.ended_at = e.ended_at
    row.position_id = e.position_id
    row.portfolio_id = e.portfolio_id
    row.baseline_price = e.baseline_price
    row.baseline_shares_equivalent = e.baseline_shares_equivalent
    row.current_portfolio_value = e.current_portfolio_value
    row.current_buyhold_value = e.current_buyhold_value
    row.evaluation_count = e.evaluation_count
    row.trade_count = e.trade_count
    row.total_commission_paid = e.total_commission_paid
    row.updated_at = e.updated_at


class SQLTradingExperimentRepo(TradingExperimentRepo):
    """SQL implementation of TradingExperimentRepo."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def get(self, tenant_id: str, experiment_id: str) -> Optional[TradingExperiment]:
        """Get an experiment by ID, scoped to tenant."""
        with self._sf() as s:
            stmt = select(TradingExperimentModel).where(
                TradingExperimentModel.id == experiment_id,
                TradingExperimentModel.tenant_id == tenant_id,
            )
            row = s.execute(stmt).scalar_one_or_none()
            if not row:
                return None
            return _to_entity(row)

    def save(self, experiment: TradingExperiment) -> None:
        """Save (create or update) an experiment."""
        with self._sf() as s:
            stmt = select(TradingExperimentModel).where(
                TradingExperimentModel.id == experiment.id,
                TradingExperimentModel.tenant_id == experiment.tenant_id,
            )
            row = s.execute(stmt).scalar_one_or_none()
            if row is None:
                # Insert new row
                new_row = _new_row_from_entity(experiment)
                s.add(new_row)
            else:
                # Update existing row
                _apply_entity_to_row(row, experiment)
            s.commit()

    def delete(self, tenant_id: str, experiment_id: str) -> bool:
        """Delete an experiment by ID. Returns True if deleted."""
        with self._sf() as s:
            stmt = select(TradingExperimentModel).where(
                TradingExperimentModel.id == experiment_id,
                TradingExperimentModel.tenant_id == tenant_id,
            )
            row = s.execute(stmt).scalar_one_or_none()
            if row is None:
                return False
            s.delete(row)
            s.commit()
            return True

    def list_all(self, tenant_id: str) -> List[TradingExperiment]:
        """List all experiments for a tenant."""
        with self._sf() as s:
            stmt = (
                select(TradingExperimentModel)
                .where(TradingExperimentModel.tenant_id == tenant_id)
                .order_by(TradingExperimentModel.created_at.desc())
            )
            rows = s.execute(stmt).scalars().all()
            return [_to_entity(r) for r in rows]

    def list_by_status(self, tenant_id: str, status: str) -> List[TradingExperiment]:
        """List experiments by status (RUNNING, PAUSED, COMPLETED)."""
        with self._sf() as s:
            stmt = (
                select(TradingExperimentModel)
                .where(
                    TradingExperimentModel.tenant_id == tenant_id,
                    TradingExperimentModel.status == status,
                )
                .order_by(TradingExperimentModel.created_at.desc())
            )
            rows = s.execute(stmt).scalars().all()
            return [_to_entity(r) for r in rows]

    def clear(self) -> None:
        """Clear all experiments (test helper)."""
        with self._sf() as s:
            s.query(TradingExperimentModel).delete()
            s.commit()

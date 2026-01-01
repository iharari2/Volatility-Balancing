# =========================
# backend/infrastructure/persistence/sql/portfolio_config_repo_sql.py
# =========================
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import select

from domain.entities.portfolio_config import PortfolioConfig
from domain.ports.portfolio_config_repo import PortfolioConfigRepo
from .models import PortfolioConfigModel


def _to_entity(m: PortfolioConfigModel) -> PortfolioConfig:
    """SQL row -> domain entity."""
    return PortfolioConfig(
        tenant_id=m.tenant_id,
        portfolio_id=m.portfolio_id,
        trigger_up_pct=m.trigger_up_pct,
        trigger_down_pct=m.trigger_down_pct,
        min_stock_pct=m.min_stock_pct,
        max_stock_pct=m.max_stock_pct,
        max_trade_pct_of_position=m.max_trade_pct_of_position,
        commission_rate_pct=m.commission_rate_pct,
        version=m.version,
        updated_at=m.updated_at,
    )


def _new_row_from_entity(c: PortfolioConfig) -> PortfolioConfigModel:
    """Domain entity -> new SQL row (insert)."""
    return PortfolioConfigModel(
        tenant_id=c.tenant_id,
        portfolio_id=c.portfolio_id,
        trigger_up_pct=c.trigger_up_pct,
        trigger_down_pct=c.trigger_down_pct,
        min_stock_pct=c.min_stock_pct,
        max_stock_pct=c.max_stock_pct,
        max_trade_pct_of_position=c.max_trade_pct_of_position,
        commission_rate_pct=c.commission_rate_pct,
        version=c.version,
        updated_at=c.updated_at,
    )


def _apply_entity_to_row(row: PortfolioConfigModel, c: PortfolioConfig) -> None:
    """Apply domain entity fields onto an existing SQL row (update)."""
    row.trigger_up_pct = c.trigger_up_pct
    row.trigger_down_pct = c.trigger_down_pct
    row.min_stock_pct = c.min_stock_pct
    row.max_stock_pct = c.max_stock_pct
    row.max_trade_pct_of_position = c.max_trade_pct_of_position
    row.commission_rate_pct = c.commission_rate_pct
    row.version = c.version
    row.updated_at = c.updated_at


class SQLPortfolioConfigRepo(PortfolioConfigRepo):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def get(self, tenant_id: str, portfolio_id: str) -> Optional[PortfolioConfig]:
        with self._sf() as s:
            stmt = select(PortfolioConfigModel).where(
                PortfolioConfigModel.tenant_id == tenant_id,
                PortfolioConfigModel.portfolio_id == portfolio_id,
            )
            row = s.execute(stmt).scalar_one_or_none()
            if not row:
                return None
            return _to_entity(row)

    def save(self, config: PortfolioConfig) -> None:
        with self._sf() as s:
            stmt = select(PortfolioConfigModel).where(
                PortfolioConfigModel.tenant_id == config.tenant_id,
                PortfolioConfigModel.portfolio_id == config.portfolio_id,
            )
            row = s.execute(stmt).scalar_one_or_none()
            if row is None:
                s.add(_new_row_from_entity(config))
            else:
                _apply_entity_to_row(row, config)
            s.commit()

    def create(
        self,
        tenant_id: str,
        portfolio_id: str,
        trigger_up_pct: float = 3.0,
        trigger_down_pct: float = -3.0,
        min_stock_pct: float = 20.0,
        max_stock_pct: float = 80.0,
        max_trade_pct_of_position: Optional[float] = None,
        commission_rate_pct: float = 0.0,
    ) -> PortfolioConfig:
        now = datetime.now(timezone.utc)
        config = PortfolioConfig(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            trigger_up_pct=trigger_up_pct,
            trigger_down_pct=trigger_down_pct,
            min_stock_pct=min_stock_pct,
            max_stock_pct=max_stock_pct,
            max_trade_pct_of_position=max_trade_pct_of_position,
            commission_rate_pct=commission_rate_pct,
            version=1,
            updated_at=now,
        )
        self.save(config)
        return config

    def delete(self, tenant_id: str, portfolio_id: str) -> bool:
        with self._sf() as s:
            stmt = select(PortfolioConfigModel).where(
                PortfolioConfigModel.tenant_id == tenant_id,
                PortfolioConfigModel.portfolio_id == portfolio_id,
            )
            row = s.execute(stmt).scalar_one_or_none()
            if row is None:
                return False
            s.delete(row)
            s.commit()
            return True

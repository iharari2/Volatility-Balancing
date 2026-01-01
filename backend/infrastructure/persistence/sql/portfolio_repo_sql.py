# =========================
# backend/infrastructure/persistence/sql/portfolio_repo_sql.py
# =========================
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import select

from domain.entities.portfolio import Portfolio
from domain.ports.portfolio_repo import PortfolioRepo
from .models import PortfolioModel, PortfolioPositionModel


def _to_entity(m: PortfolioModel) -> Portfolio:
    """SQL row -> domain entity."""
    return Portfolio(
        id=m.id,
        tenant_id=m.tenant_id,
        name=m.name,
        description=m.description,
        user_id=m.user_id,
        type=m.type,
        trading_state=m.trading_state,
        trading_hours_policy=m.trading_hours_policy,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _new_row_from_entity(p: Portfolio) -> PortfolioModel:
    """Domain entity -> new SQL row (insert)."""
    return PortfolioModel(
        id=p.id,
        tenant_id=p.tenant_id,
        name=p.name,
        description=p.description,
        user_id=p.user_id,
        type=p.type,
        trading_state=p.trading_state,
        trading_hours_policy=p.trading_hours_policy,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _apply_entity_to_row(row: PortfolioModel, p: Portfolio) -> None:
    """Update existing SQL row with domain entity data."""
    row.name = p.name
    row.description = p.description
    row.user_id = p.user_id
    row.type = p.type
    row.trading_state = p.trading_state
    row.trading_hours_policy = p.trading_hours_policy
    row.updated_at = p.updated_at


class SQLPortfolioRepo(PortfolioRepo):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    # --- Reads ---

    def get(self, tenant_id: str, portfolio_id: str) -> Optional[Portfolio]:
        with self._sf() as s:
            stmt = select(PortfolioModel).where(
                PortfolioModel.tenant_id == tenant_id,
                PortfolioModel.id == portfolio_id,
            )
            row = s.execute(stmt).scalar_one_or_none()
            if not row:
                return None
            return _to_entity(row)

    def list_all(self, tenant_id: str, user_id: Optional[str] = None) -> List[Portfolio]:
        with self._sf() as s:
            stmt = select(PortfolioModel).where(PortfolioModel.tenant_id == tenant_id)
            if user_id:
                stmt = stmt.where(PortfolioModel.user_id == user_id)
            stmt = stmt.order_by(PortfolioModel.created_at.desc())
            rows = s.execute(stmt).scalars().all()
            return [_to_entity(r) for r in rows]

    def get_position_ids(self, tenant_id: str, portfolio_id: str) -> List[str]:
        """Get all position IDs in a portfolio."""
        with self._sf() as s:
            stmt = select(PortfolioPositionModel.position_id).where(
                PortfolioPositionModel.portfolio_id == portfolio_id
            )
            rows = s.execute(stmt).scalars().all()
            return list(rows)

    # --- Writes ---

    def save(self, portfolio: Portfolio) -> None:
        with self._sf() as s:
            stmt = select(PortfolioModel).where(
                PortfolioModel.tenant_id == portfolio.tenant_id,
                PortfolioModel.id == portfolio.id,
            )
            row = s.execute(stmt).scalar_one_or_none()
            if row is None:
                s.add(_new_row_from_entity(portfolio))
            else:
                _apply_entity_to_row(row, portfolio)
            s.commit()

    def create(
        self,
        tenant_id: str,
        name: str,
        description: Optional[str] = None,
        user_id: str = "default",
        portfolio_type: str = "LIVE",
        trading_state: str = "NOT_CONFIGURED",
        trading_hours_policy: str = "OPEN_ONLY",
    ) -> Portfolio:
        """Create + persist a new Portfolio."""
        now = datetime.now(timezone.utc)
        portfolio = Portfolio(
            id=f"pf_{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            name=name,
            description=description,
            user_id=user_id,
            type=portfolio_type,
            trading_state=trading_state,
            trading_hours_policy=trading_hours_policy,
            created_at=now,
            updated_at=now,
        )
        self.save(portfolio)
        return portfolio

    def delete(self, tenant_id: str, portfolio_id: str) -> bool:
        """Delete a portfolio by ID, scoped to tenant. Returns True if deleted, False if not found."""
        with self._sf() as s:
            stmt = select(PortfolioModel).where(
                PortfolioModel.tenant_id == tenant_id,
                PortfolioModel.id == portfolio_id,
            )
            row = s.execute(stmt).scalar_one_or_none()
            if not row:
                return False
            s.delete(row)
            s.commit()
            return True

    def add_position(self, tenant_id: str, portfolio_id: str, position_id: str) -> bool:
        """Add a position to a portfolio. Returns True if added, False if already exists."""
        with self._sf() as s:
            # Check if portfolio exists
            stmt = select(PortfolioModel).where(
                PortfolioModel.tenant_id == tenant_id,
                PortfolioModel.id == portfolio_id,
            )
            portfolio = s.execute(stmt).scalar_one_or_none()
            if not portfolio:
                return False

            # Check if already exists
            stmt = select(PortfolioPositionModel).where(
                PortfolioPositionModel.portfolio_id == portfolio_id,
                PortfolioPositionModel.position_id == position_id,
            )
            existing = s.execute(stmt).scalar_one_or_none()
            if existing:
                return False

            # Add the position
            portfolio_position = PortfolioPositionModel(
                portfolio_id=portfolio_id,
                position_id=position_id,
                created_at=datetime.now(timezone.utc),
            )
            s.add(portfolio_position)
            s.commit()
            return True

    def remove_position(self, tenant_id: str, portfolio_id: str, position_id: str) -> bool:
        """Remove a position from a portfolio. Returns True if removed, False if not found."""
        with self._sf() as s:
            stmt = select(PortfolioPositionModel).where(
                PortfolioPositionModel.portfolio_id == portfolio_id,
                PortfolioPositionModel.position_id == position_id,
            )
            row = s.execute(stmt).scalar_one_or_none()
            if not row:
                return False
            s.delete(row)
            s.commit()
            return True

    def clear(self) -> None:
        """Clear all portfolios (for testing)."""
        with self._sf() as s:
            s.query(PortfolioPositionModel).delete()
            s.query(PortfolioModel).delete()
            s.commit()

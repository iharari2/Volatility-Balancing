# =========================
# backend/infrastructure/persistence/sql/portfolio_state_repo_sql.py
# =========================
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from .models import PortfolioStateModel


class PortfolioState:
    """Domain entity for portfolio state."""

    def __init__(
        self,
        id: str,
        name: str,
        description: Optional[str] = None,
        initial_cash: float = 0.0,
        initial_asset_value: float = 0.0,
        initial_asset_units: float = 0.0,
        current_cash: float = 0.0,
        current_asset_value: float = 0.0,
        current_asset_units: float = 0.0,
        ticker: str = "",
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.initial_cash = initial_cash
        self.initial_asset_value = initial_asset_value
        self.initial_asset_units = initial_asset_units
        self.current_cash = current_cash
        self.current_asset_value = current_asset_value
        self.current_asset_units = current_asset_units
        self.ticker = ticker
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)


def _to_entity(m: PortfolioStateModel) -> PortfolioState:
    """SQL row -> domain entity."""
    return PortfolioState(
        id=m.id,
        name=m.name,
        description=m.description,
        initial_cash=m.initial_cash,
        initial_asset_value=m.initial_asset_value,
        initial_asset_units=m.initial_asset_units,
        current_cash=m.current_cash,
        current_asset_value=m.current_asset_value,
        current_asset_units=m.current_asset_units,
        ticker=m.ticker,
        is_active=m.is_active,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _new_row_from_entity(p: PortfolioState) -> PortfolioStateModel:
    """Domain entity -> new SQL row (insert)."""
    return PortfolioStateModel(
        id=p.id,
        name=p.name,
        description=p.description,
        initial_cash=p.initial_cash,
        initial_asset_value=p.initial_asset_value,
        initial_asset_units=p.initial_asset_units,
        current_cash=p.current_cash,
        current_asset_value=p.current_asset_value,
        current_asset_units=p.current_asset_units,
        ticker=p.ticker,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _apply_entity_to_row(row: PortfolioStateModel, p: PortfolioState) -> None:
    """Update existing SQL row with domain entity data."""
    row.name = p.name
    row.description = p.description
    row.initial_cash = p.initial_cash
    row.initial_asset_value = p.initial_asset_value
    row.initial_asset_units = p.initial_asset_units
    row.current_cash = p.current_cash
    row.current_asset_value = p.current_asset_value
    row.current_asset_units = p.current_asset_units
    row.ticker = p.ticker
    row.is_active = p.is_active
    row.updated_at = p.updated_at


class SQLPortfolioStateRepo:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    # --- Reads ---

    def get(self, state_id: str) -> Optional[PortfolioState]:
        with self._sf() as s:
            row = s.get(PortfolioStateModel, state_id)
            if not row:
                return None
            return _to_entity(row)

    def get_active(self) -> Optional[PortfolioState]:
        with self._sf() as s:
            row = (
                s.query(PortfolioStateModel)
                .filter(PortfolioStateModel.is_active)
                .order_by(PortfolioStateModel.updated_at.desc())
                .first()
            )
            if not row:
                return None
            return _to_entity(row)

    def list_all(self, limit: int = 100, offset: int = 0) -> List[PortfolioState]:
        with self._sf() as s:
            rows = (
                s.query(PortfolioStateModel)
                .order_by(PortfolioStateModel.updated_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [_to_entity(r) for r in rows]

    # --- Writes ---

    def save(self, state: PortfolioState) -> None:
        with self._sf() as s:
            row = s.get(PortfolioStateModel, state.id)
            if row is None:
                s.add(_new_row_from_entity(state))
            else:
                _apply_entity_to_row(row, state)
            s.commit()

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        initial_cash: float = 0.0,
        initial_asset_value: float = 0.0,
        initial_asset_units: float = 0.0,
        current_cash: float = 0.0,
        current_asset_value: float = 0.0,
        current_asset_units: float = 0.0,
        ticker: str = "",
    ) -> PortfolioState:
        """Create + persist a new PortfolioState."""
        now = datetime.now(timezone.utc)
        state = PortfolioState(
            id=f"ps_{uuid4().hex[:8]}",
            name=name,
            description=description,
            initial_cash=initial_cash,
            initial_asset_value=initial_asset_value,
            initial_asset_units=initial_asset_units,
            current_cash=current_cash,
            current_asset_value=current_asset_value,
            current_asset_units=current_asset_units,
            ticker=ticker,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.save(state)
        return state

    def deactivate_all(self) -> None:
        """Deactivate all portfolio states."""
        with self._sf() as s:
            s.query(PortfolioStateModel).update(
                {"is_active": False, "updated_at": datetime.now(timezone.utc)}
            )
            s.commit()

    def clear(self) -> None:
        """Wipe all portfolio states (test helper / dev)."""
        with self._sf() as s:
            s.query(PortfolioStateModel).delete()
            s.commit()

# =========================
# backend/infrastructure/persistence/memory/portfolio_state_repo_mem.py
# =========================
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, List

from infrastructure.persistence.sql.portfolio_state_repo_sql import PortfolioState


class InMemoryPortfolioStateRepo:
    def __init__(self) -> None:
        self._items: Dict[str, PortfolioState] = {}

    def get(self, state_id: str) -> Optional[PortfolioState]:
        return self._items.get(state_id)

    def get_active(self) -> Optional[PortfolioState]:
        """Get the currently active portfolio state."""
        for state in self._items.values():
            if state.is_active:
                return state
        return None

    def list_all(self, limit: int = 100, offset: int = 0) -> List[PortfolioState]:
        """List all portfolio states, ordered by updated_at desc."""
        states = list(self._items.values())
        states.sort(key=lambda x: x.updated_at, reverse=True)
        return states[offset : offset + limit]

    def save(self, state: PortfolioState) -> None:
        state.updated_at = datetime.now(timezone.utc)
        self._items[state.id] = state

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
        """Create a new portfolio state."""
        now = datetime.now(timezone.utc)
        state = PortfolioState(
            id=f"ps_{uuid.uuid4().hex[:8]}",
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
        now = datetime.now(timezone.utc)
        for state in self._items.values():
            state.is_active = False
            state.updated_at = now

    def clear(self) -> None:
        """Clear all portfolio states."""
        self._items.clear()

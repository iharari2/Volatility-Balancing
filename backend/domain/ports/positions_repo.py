# =========================
# backend/domain/ports/positions_repo.py
# =========================

from typing import Protocol, Optional, List
from domain.entities.position import Position


class PositionsRepo(Protocol):
    """Repository interface for Position entities. All methods require tenant_id and portfolio_id."""

    def get(self, tenant_id: str, portfolio_id: str, position_id: str) -> Optional[Position]:
        """Get a position by ID, scoped to tenant and portfolio."""
        ...

    def create(
        self,
        tenant_id: str,
        portfolio_id: str,
        asset_symbol: str,
        qty: float,
        anchor_price: Optional[float] = None,
        avg_cost: Optional[float] = None,
    ) -> Position:
        """Create a new position, scoped to tenant and portfolio."""
        ...

    def save(self, position: Position) -> None:
        """Save (create or update) a position."""
        ...

    def delete(self, tenant_id: str, portfolio_id: str, position_id: str) -> bool:
        """Delete a position by ID, scoped to tenant and portfolio."""
        ...

    def list_all(self, tenant_id: str, portfolio_id: str) -> List[Position]:
        """List all positions for a tenant and portfolio."""
        ...

    def get_by_asset(
        self, tenant_id: str, portfolio_id: str, asset_symbol: str
    ) -> Optional[Position]:
        """Get a position by asset symbol, scoped to tenant and portfolio."""
        ...

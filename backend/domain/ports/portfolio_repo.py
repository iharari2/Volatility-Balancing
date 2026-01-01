# =========================
# backend/domain/ports/portfolio_repo.py
# =========================

from typing import Protocol, Optional, List
from domain.entities.portfolio import Portfolio


class PortfolioRepo(Protocol):
    """Repository interface for Portfolio entities. All methods require tenant_id."""

    def get(self, tenant_id: str, portfolio_id: str) -> Optional[Portfolio]:
        """Get a portfolio by ID, scoped to tenant."""
        ...

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
        """Create a new portfolio, scoped to tenant."""
        ...

    def save(self, portfolio: Portfolio) -> None:
        """Save (create or update) a portfolio."""
        ...

    def delete(self, tenant_id: str, portfolio_id: str) -> bool:
        """Delete a portfolio by ID, scoped to tenant. Returns True if deleted, False if not found."""
        ...

    def list_all(self, tenant_id: str, user_id: Optional[str] = None) -> List[Portfolio]:
        """List all portfolios for a tenant, optionally filtered by user_id."""
        ...

    def add_position(self, tenant_id: str, portfolio_id: str, position_id: str) -> bool:
        """Add a position to a portfolio. Returns True if added, False if already exists."""
        ...

    def remove_position(self, tenant_id: str, portfolio_id: str, position_id: str) -> bool:
        """Remove a position from a portfolio. Returns True if removed, False if not found."""
        ...

    def get_position_ids(self, tenant_id: str, portfolio_id: str) -> List[str]:
        """Get all position IDs in a portfolio."""
        ...

    def clear(self) -> None:
        """Clear all portfolios (for testing)."""
        ...

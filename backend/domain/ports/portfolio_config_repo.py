# =========================
# backend/domain/ports/portfolio_config_repo.py
# =========================

from typing import Protocol, Optional
from domain.entities.portfolio_config import PortfolioConfig


class PortfolioConfigRepo(Protocol):
    """Repository interface for PortfolioConfig entities."""

    def get(self, tenant_id: str, portfolio_id: str) -> Optional[PortfolioConfig]:
        """Get configuration for a portfolio."""
        ...

    def save(self, config: PortfolioConfig) -> None:
        """Save (create or update) configuration."""
        ...

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
        """Create a new configuration record."""
        ...

    def delete(self, tenant_id: str, portfolio_id: str) -> bool:
        """Delete configuration for a portfolio. Returns True if deleted, False if not found."""
        ...

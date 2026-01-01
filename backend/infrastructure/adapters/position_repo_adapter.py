# =========================
# backend/infrastructure/adapters/position_repo_adapter.py
# =========================
"""Adapter implementing IPositionRepository using existing PositionsRepo."""

from typing import Iterable, Optional

from application.ports.repos import IPositionRepository
from domain.ports.positions_repo import PositionsRepo
from domain.ports.portfolio_repo import PortfolioRepo
from domain.value_objects.position_state import PositionState
from infrastructure.adapters.converters import position_to_position_state


class PositionRepoAdapter(IPositionRepository):
    """Adapter that implements IPositionRepository using existing PositionsRepo."""

    def __init__(
        self,
        positions_repo: PositionsRepo,
        portfolio_repo: Optional[PortfolioRepo] = None,
        default_tenant_id: str = "default",
    ):
        """
        Initialize adapter with existing positions repository.

        Args:
            positions_repo: Existing PositionsRepo implementation (SQL or Memory)
            portfolio_repo: Portfolio repository to get active portfolios (optional, for trading)
            default_tenant_id: Default tenant ID to use when portfolio_repo is not available
        """
        self.positions_repo = positions_repo
        self.portfolio_repo = portfolio_repo
        self.default_tenant_id = default_tenant_id

    def get_active_positions_for_trading(self) -> Iterable[str]:
        """Return identifiers for positions that should be considered in live trading.

        Iterates over portfolios in RUNNING state and returns all positions with anchor_price set.
        """
        position_ids = []

        if self.portfolio_repo:
            # Get all portfolios for default tenant (or iterate over all tenants if needed)
            # For now, use default tenant. In production, this should iterate over all tenants
            portfolios = self.portfolio_repo.list_all(tenant_id=self.default_tenant_id)

            # Filter to only RUNNING portfolios
            running_portfolios = [p for p in portfolios if p.trading_state == "RUNNING"]

            # Get positions for each running portfolio
            for portfolio in running_portfolios:
                positions = self.positions_repo.list_all(
                    tenant_id=portfolio.tenant_id,
                    portfolio_id=portfolio.id,
                )
                # Only include positions with anchor_price set
                position_ids.extend([pos.id for pos in positions if pos.anchor_price is not None])
        else:
            # Fallback: if no portfolio_repo, we can't get portfolio-scoped positions
            # This is a legacy mode that shouldn't be used in production
            # Return empty list to avoid errors
            return []

        return position_ids

    def load_position_state(self, position_id: str) -> PositionState:
        """Load position state for a position.

        Note: This method needs tenant_id and portfolio_id, but the interface only provides position_id.
        We'll need to search across portfolios or update the interface.
        For now, this is a limitation - we'll need to update the interface or find position by ID.
        """
        # TODO: This is a problem - we need tenant_id and portfolio_id to get a position
        # but the interface only provides position_id. We need to either:
        # 1. Update the interface to include tenant_id and portfolio_id
        # 2. Search across all portfolios (inefficient)
        # 3. Store a mapping of position_id -> (tenant_id, portfolio_id)

        # For now, try to find the position by searching portfolios
        # This is inefficient but works for the transition period
        if self.portfolio_repo:
            portfolios = self.portfolio_repo.list_all(tenant_id=self.default_tenant_id)
            for portfolio in portfolios:
                position = self.positions_repo.get(
                    tenant_id=portfolio.tenant_id,
                    portfolio_id=portfolio.id,
                    position_id=position_id,
                )
                if position:
                    # Cash lives in Position entity (cash lives in PositionCell per target state model)
                    cash = position.cash or 0.0
                    return position_to_position_state(position, cash=cash)

        raise KeyError(f"Position not found: {position_id}")

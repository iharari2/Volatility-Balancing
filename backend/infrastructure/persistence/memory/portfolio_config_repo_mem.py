from typing import Dict, Optional, Tuple
from domain.entities.portfolio_config import PortfolioConfig


class InMemoryPortfolioConfigRepo:
    def __init__(self) -> None:
        self._store: Dict[Tuple[str, str], PortfolioConfig] = {}

    def get(self, tenant_id: str, portfolio_id: str) -> Optional[PortfolioConfig]:
        return self._store.get((tenant_id, portfolio_id))

    def save(self, config: PortfolioConfig) -> None:
        self._store[(config.tenant_id, config.portfolio_id)] = config

    def create(
        self,
        tenant_id: str,
        portfolio_id: str,
        trigger_up_pct: float = 3.0,
        trigger_down_pct: float = -3.0,
        min_stock_pct: float = 25.0,
        max_stock_pct: float = 75.0,
        max_trade_pct_of_position: Optional[float] = None,
        commission_rate_pct: float = 0.01,
    ) -> PortfolioConfig:
        config = PortfolioConfig(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            trigger_up_pct=trigger_up_pct,
            trigger_down_pct=trigger_down_pct,
            min_stock_pct=min_stock_pct,
            max_stock_pct=max_stock_pct,
            max_trade_pct_of_position=max_trade_pct_of_position,
            commission_rate_pct=commission_rate_pct,
        )
        self._store[(tenant_id, portfolio_id)] = config
        return config

    def delete(self, tenant_id: str, portfolio_id: str) -> bool:
        key = (tenant_id, portfolio_id)
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()

# =========================
# backend/domain/entities/portfolio_config.py
# =========================
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class PortfolioConfig:
    """Domain entity representing configuration for a portfolio."""

    tenant_id: str
    portfolio_id: str
    trigger_up_pct: float = 3.0
    trigger_down_pct: float = -3.0
    min_stock_pct: float = 20.0
    max_stock_pct: float = 80.0
    max_trade_pct_of_position: Optional[float] = None
    commission_rate_pct: float = 0.0
    version: int = 1
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update(
        self,
        trigger_up_pct: Optional[float] = None,
        trigger_down_pct: Optional[float] = None,
        min_stock_pct: Optional[float] = None,
        max_stock_pct: Optional[float] = None,
        max_trade_pct_of_position: Optional[float] = None,
        commission_rate_pct: Optional[float] = None,
    ) -> None:
        """Update configuration fields."""
        if trigger_up_pct is not None:
            self.trigger_up_pct = trigger_up_pct
        if trigger_down_pct is not None:
            self.trigger_down_pct = trigger_down_pct
        if min_stock_pct is not None:
            self.min_stock_pct = min_stock_pct
        if max_stock_pct is not None:
            self.max_stock_pct = max_stock_pct
        if max_trade_pct_of_position is not None:
            self.max_trade_pct_of_position = max_trade_pct_of_position
        if commission_rate_pct is not None:
            self.commission_rate_pct = commission_rate_pct
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)

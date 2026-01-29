# =========================
# backend/domain/entities/simulation_result.py
# =========================

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4


@dataclass
class SimulationResult:
    """Result of a simulation run."""

    id: UUID
    ticker: str
    start_date: str
    end_date: str
    total_trading_days: int
    initial_cash: float

    # Algorithm performance
    algorithm_trades: int
    algorithm_pnl: float
    algorithm_return_pct: float
    algorithm_volatility: float
    algorithm_sharpe_ratio: float
    algorithm_max_drawdown: float

    # Buy & Hold performance
    buy_hold_pnl: float
    buy_hold_return_pct: float
    buy_hold_volatility: float
    buy_hold_sharpe_ratio: float
    buy_hold_max_drawdown: float

    # Comparison metrics
    excess_return: float
    alpha: float
    beta: float
    information_ratio: float

    # Trade details
    trade_log: List[Dict[str, Any]] = field(default_factory=list)
    daily_returns: List[Dict[str, Any]] = field(default_factory=list)

    # Dividend data
    dividend_analysis: Optional[Dict[str, Any]] = None

    # Market data for visualization
    price_data: List[Dict[str, Any]] = field(default_factory=list)

    # Trigger analysis
    trigger_analysis: List[Dict[str, Any]] = field(default_factory=list)

    # Comprehensive time-series data
    time_series_data: List[Dict[str, Any]] = field(default_factory=list)

    # Debug info
    debug_info: Optional[List[Dict[str, Any]]] = None

    created_at: datetime = None

    def __post_init__(self):
        """Initialize timestamps."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

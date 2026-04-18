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

    @classmethod
    def create(
        cls,
        ticker: str,
        start_date: str,
        end_date: str,
        metrics: Dict[str, Any],
        raw_data: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> "SimulationResult":
        """Factory that accepts the metrics/raw_data dict shape used by excel_export routes."""
        return cls(
            id=uuid4(),
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            total_trading_days=raw_data.get("total_trading_days", 0),
            initial_cash=raw_data.get("initial_cash", 100000.0),
            algorithm_trades=raw_data.get("algorithm_trades", 0),
            algorithm_pnl=metrics.get("algorithm_pnl", 0.0),
            algorithm_return_pct=metrics.get("total_return", metrics.get("algorithm_return_pct", 0.0)),
            algorithm_volatility=metrics.get("volatility", metrics.get("algorithm_volatility", 0.0)),
            algorithm_sharpe_ratio=metrics.get("sharpe_ratio", metrics.get("algorithm_sharpe_ratio", 0.0)),
            algorithm_max_drawdown=metrics.get("max_drawdown", metrics.get("algorithm_max_drawdown", 0.0)),
            buy_hold_pnl=metrics.get("buy_hold_pnl", 0.0),
            buy_hold_return_pct=metrics.get("buy_hold_return_pct", 0.0),
            buy_hold_volatility=metrics.get("buy_hold_volatility", 0.0),
            buy_hold_sharpe_ratio=metrics.get("buy_hold_sharpe_ratio", 0.0),
            buy_hold_max_drawdown=metrics.get("buy_hold_max_drawdown", 0.0),
            excess_return=metrics.get("excess_return", 0.0),
            alpha=metrics.get("alpha", 0.0),
            beta=metrics.get("beta", 1.0),
            information_ratio=metrics.get("information_ratio", 0.0),
            trade_log=raw_data.get("trade_log", []),
            daily_returns=raw_data.get("daily_returns", []),
            price_data=raw_data.get("price_data", []),
            trigger_analysis=raw_data.get("trigger_analysis", []),
            time_series_data=raw_data.get("time_series_data", []),
        )

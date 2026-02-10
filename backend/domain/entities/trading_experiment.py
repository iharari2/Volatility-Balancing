# backend/domain/entities/trading_experiment.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TradingExperiment:
    """
    Entity representing a multi-day trading experiment.

    Tracks portfolio performance against buy-and-hold baseline to measure
    the effectiveness of the trading strategy over time.
    """
    id: str
    tenant_id: str
    name: str
    ticker: str
    initial_capital: float

    # Status: RUNNING, PAUSED, COMPLETED
    status: str = "RUNNING"
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    # Position reference (created when experiment starts)
    position_id: str = ""
    portfolio_id: str = ""

    # Buy-and-hold baseline (captured at start)
    baseline_price: float = 0.0
    baseline_shares_equivalent: float = 0.0  # initial_capital / baseline_price

    # Running metrics (updated each evaluation)
    current_portfolio_value: float = 0.0
    current_buyhold_value: float = 0.0
    evaluation_count: int = 0
    trade_count: int = 0
    total_commission_paid: float = 0.0

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def calculate_buyhold_value(self, current_price: float) -> float:
        """Calculate buy-and-hold value at current price."""
        return self.baseline_shares_equivalent * current_price

    def get_portfolio_return_pct(self) -> float:
        """Calculate portfolio return percentage."""
        if self.initial_capital <= 0:
            return 0.0
        return ((self.current_portfolio_value - self.initial_capital) / self.initial_capital) * 100

    def get_buyhold_return_pct(self) -> float:
        """Calculate buy-and-hold return percentage."""
        if self.initial_capital <= 0:
            return 0.0
        return ((self.current_buyhold_value - self.initial_capital) / self.initial_capital) * 100

    def get_excess_return_pct(self) -> float:
        """Calculate excess return (portfolio vs buy-and-hold)."""
        return self.get_portfolio_return_pct() - self.get_buyhold_return_pct()

    def get_days_running(self) -> int:
        """Calculate number of days the experiment has been running."""
        end_time = self.ended_at or datetime.now(timezone.utc)
        delta = end_time - self.started_at
        return max(1, delta.days)

    def update_metrics(
        self,
        current_price: float,
        portfolio_value: float,
        trade_executed: bool = False,
        commission: float = 0.0,
    ) -> None:
        """Update experiment metrics after an evaluation."""
        self.current_portfolio_value = portfolio_value
        self.current_buyhold_value = self.calculate_buyhold_value(current_price)
        self.evaluation_count += 1
        if trade_executed:
            self.trade_count += 1
            self.total_commission_paid += commission
        self.updated_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        """Mark the experiment as completed."""
        self.status = "COMPLETED"
        self.ended_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def pause(self) -> None:
        """Pause the experiment."""
        self.status = "PAUSED"
        self.updated_at = datetime.now(timezone.utc)

    def resume(self) -> None:
        """Resume a paused experiment."""
        self.status = "RUNNING"
        self.updated_at = datetime.now(timezone.utc)

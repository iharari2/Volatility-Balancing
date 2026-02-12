# backend/application/dto/explainability.py
"""
Data Transfer Objects for the Explainability Table feature.

These DTOs represent the unified timeline view for both live trading
and simulation modes. Supports the complete trade lifecycle:
market data → trigger evaluation → guardrail checks → order submission →
execution → position impact.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class ExplainabilityRow:
    """
    A single row in the explainability timeline.

    Represents one evaluation point (timestamp) with all the data needed
    to understand why a trading decision was made. This unified view shows
    the complete trade lifecycle from market data through execution and
    position impact.
    """

    # ========== Group 1: Time & Identity ==========
    timestamp: datetime
    date_str: str  # YYYY-MM-DD format for grouping
    trace_id: Optional[str] = None  # Correlates related events

    # ========== Group 2: Market Data ==========
    price: float = 0.0  # Effective price used for calculations
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: Optional[float] = None
    volume: Optional[float] = None

    # ========== Group 3: Trigger Evaluation ==========
    anchor_price: Optional[float] = None
    delta_pct: Optional[float] = None  # (price - anchor) / anchor * 100
    trigger_up_threshold: Optional[float] = None  # e.g., 5.0 = +5%
    trigger_down_threshold: Optional[float] = None  # e.g., -5.0 = -5%
    trigger_fired: bool = False  # Did price cross a threshold?
    trigger_direction: Optional[str] = None  # UP, DOWN, or NONE
    trigger_reason: Optional[str] = None  # Human explanation

    # ========== Group 4: Guardrails ==========
    min_stock_pct: Optional[float] = None
    max_stock_pct: Optional[float] = None
    current_stock_pct: Optional[float] = None  # Stock % before potential trade
    guardrail_allowed: bool = True
    guardrail_block_reason: Optional[str] = None

    # ========== Group 5: Action Decision ==========
    action: str = "HOLD"  # BUY / SELL / HOLD / SKIP
    action_reason: Optional[str] = None  # Human-readable reason
    intended_qty: Optional[float] = None  # Shares intended to trade
    intended_value: Optional[float] = None  # Notional value of intended trade

    # ========== Group 6: Order Status ==========
    order_id: Optional[str] = None  # Internal order ID (null if HOLD/SKIP)
    order_status: Optional[str] = None  # created, submitted, pending, working, partial, filled, rejected, cancelled
    broker_order_id: Optional[str] = None  # Broker's order identifier
    broker_status: Optional[str] = None  # Broker's status string

    # ========== Group 7: Execution Details ==========
    execution_price: Optional[float] = None  # Average fill price
    execution_qty: Optional[float] = None  # Total shares executed
    execution_value: Optional[float] = None  # execution_qty * execution_price
    commission: Optional[float] = None  # Total commission
    execution_status: Optional[str] = None  # FILLED, PARTIAL, NONE

    # ========== Group 8: Position Impact (Before → After) ==========
    qty_before: Optional[float] = None  # Shares before this evaluation
    qty_after: Optional[float] = None  # Shares after (if executed)
    cash_before: Optional[float] = None
    cash_after: Optional[float] = None  # Includes commission deduction
    stock_value_before: Optional[float] = None  # qty_before * price
    stock_value_after: Optional[float] = None  # qty_after * price
    total_value_before: Optional[float] = None  # stock_value + cash before
    total_value_after: Optional[float] = None  # stock_value + cash after
    stock_pct_before: Optional[float] = None  # Allocation % before
    stock_pct_after: Optional[float] = None  # Allocation % after

    # ========== Group 9: Dividends ==========
    dividend_declared: bool = False  # Was a dividend declared?
    dividend_ex_date: Optional[str] = None  # Ex-dividend date
    dividend_pay_date: Optional[str] = None  # Payment date
    dividend_rate: Optional[float] = None  # Dividend per share
    dividend_gross: Optional[float] = None  # Gross dividend: qty * rate
    dividend_tax: Optional[float] = None  # Withholding tax amount
    dividend_net: Optional[float] = None  # Net dividend received
    dividend_applied: bool = False  # Has dividend been credited?

    # ========== Group 10: Anchor Tracking ==========
    anchor_reset: bool = False  # Was anchor reset on this evaluation?
    anchor_old_value: Optional[float] = None  # Previous anchor before reset
    anchor_reset_reason: Optional[str] = None  # Why anchor was reset

    # ========== Legacy/Convenience Fields ==========
    # These are kept for backward compatibility with existing code
    qty: float = 0.0  # Share quantity (maps to qty_after or qty_before)
    stock_value: float = 0.0  # qty * price
    cash: float = 0.0
    total_value: float = 0.0  # stock_value + cash
    stock_pct: Optional[float] = None  # Allocation percentage

    # ========== Source Metadata ==========
    mode: str = "LIVE"  # LIVE or SIMULATION
    simulation_run_id: Optional[str] = None
    position_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    symbol: Optional[str] = None
    evaluation_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            # Group 1: Time & Identity
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "date": self.date_str,
            "trace_id": self.trace_id,

            # Group 2: Market Data
            "price": self.price,
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "volume": self.volume,

            # Group 3: Trigger Evaluation
            "anchor_price": self.anchor_price,
            "delta_pct": round(self.delta_pct, 4) if self.delta_pct is not None else None,
            "trigger_up_threshold": self.trigger_up_threshold,
            "trigger_down_threshold": self.trigger_down_threshold,
            "trigger_fired": self.trigger_fired,
            "trigger_direction": self.trigger_direction,
            "trigger_reason": self.trigger_reason,

            # Group 4: Guardrails
            "min_stock_pct": self.min_stock_pct,
            "max_stock_pct": self.max_stock_pct,
            "current_stock_pct": round(self.current_stock_pct, 2) if self.current_stock_pct is not None else None,
            "guardrail_allowed": self.guardrail_allowed,
            "guardrail_block_reason": self.guardrail_block_reason,

            # Group 5: Action Decision
            "action": self.action,
            "action_reason": self.action_reason,
            "intended_qty": round(self.intended_qty, 4) if self.intended_qty is not None else None,
            "intended_value": round(self.intended_value, 2) if self.intended_value is not None else None,

            # Group 6: Order Status
            "order_id": self.order_id,
            "order_status": self.order_status,
            "broker_order_id": self.broker_order_id,
            "broker_status": self.broker_status,

            # Group 7: Execution Details
            "execution_price": self.execution_price,
            "execution_qty": round(self.execution_qty, 4) if self.execution_qty is not None else None,
            "execution_value": round(self.execution_value, 2) if self.execution_value is not None else None,
            "commission": round(self.commission, 4) if self.commission is not None else None,
            "execution_status": self.execution_status,

            # Group 8: Position Impact
            "qty_before": round(self.qty_before, 4) if self.qty_before is not None else None,
            "qty_after": round(self.qty_after, 4) if self.qty_after is not None else None,
            "cash_before": round(self.cash_before, 2) if self.cash_before is not None else None,
            "cash_after": round(self.cash_after, 2) if self.cash_after is not None else None,
            "stock_value_before": round(self.stock_value_before, 2) if self.stock_value_before is not None else None,
            "stock_value_after": round(self.stock_value_after, 2) if self.stock_value_after is not None else None,
            "total_value_before": round(self.total_value_before, 2) if self.total_value_before is not None else None,
            "total_value_after": round(self.total_value_after, 2) if self.total_value_after is not None else None,
            "stock_pct_before": round(self.stock_pct_before, 2) if self.stock_pct_before is not None else None,
            "stock_pct_after": round(self.stock_pct_after, 2) if self.stock_pct_after is not None else None,

            # Group 9: Dividends
            "dividend_declared": self.dividend_declared,
            "dividend_ex_date": self.dividend_ex_date,
            "dividend_pay_date": self.dividend_pay_date,
            "dividend_rate": round(self.dividend_rate, 4) if self.dividend_rate is not None else None,
            "dividend_gross": round(self.dividend_gross, 2) if self.dividend_gross is not None else None,
            "dividend_tax": round(self.dividend_tax, 2) if self.dividend_tax is not None else None,
            "dividend_net": round(self.dividend_net, 2) if self.dividend_net is not None else None,
            "dividend_applied": self.dividend_applied,

            # Group 10: Anchor Tracking
            "anchor_reset": self.anchor_reset,
            "anchor_old_value": self.anchor_old_value,
            "anchor_reset_reason": self.anchor_reset_reason,

            # Legacy/Convenience fields
            "qty": self.qty,
            "stock_value": round(self.stock_value, 2),
            "cash": round(self.cash, 2),
            "total_value": round(self.total_value, 2),
            "stock_pct": round(self.stock_pct, 2) if self.stock_pct is not None else None,

            # Metadata
            "mode": self.mode,
            "simulation_run_id": self.simulation_run_id,
            "position_id": self.position_id,
            "portfolio_id": self.portfolio_id,
            "symbol": self.symbol,
            "evaluation_id": self.evaluation_id,
        }


@dataclass
class ExplainabilityTimeline:
    """
    Response container for explainability timeline data.
    """

    rows: List[ExplainabilityRow] = field(default_factory=list)
    total_rows: int = 0
    filtered_rows: int = 0

    # Pagination metadata
    offset: int = 0
    limit: int = 500

    # Query metadata
    position_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    simulation_run_id: Optional[str] = None
    symbol: Optional[str] = None
    mode: Optional[str] = None

    # Filter metadata
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    actions_filter: Optional[List[str]] = None
    order_status_filter: Optional[List[str]] = None
    aggregation: str = "daily"  # "daily" or "all"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "rows": [row.to_dict() for row in self.rows],
            "total_rows": self.total_rows,
            "filtered_rows": self.filtered_rows,
            "offset": self.offset,
            "limit": self.limit,
            "position_id": self.position_id,
            "portfolio_id": self.portfolio_id,
            "simulation_run_id": self.simulation_run_id,
            "symbol": self.symbol,
            "mode": self.mode,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "actions_filter": self.actions_filter,
            "order_status_filter": self.order_status_filter,
            "aggregation": self.aggregation,
        }

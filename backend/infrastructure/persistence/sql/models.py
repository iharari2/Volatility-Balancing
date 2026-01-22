# backend/infrastructure/persistence/sql/models.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import (
    String,
    Float,
    Integer,
    DateTime,
    UniqueConstraint,
    create_engine,
    JSON,
    Index,
    Text,
    CheckConstraint,
    Boolean,
    ForeignKey,
    ForeignKeyConstraint,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PositionModel(Base):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    portfolio_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    asset_symbol: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Renamed from ticker for clarity
    # Legacy ticker column - kept for backward compatibility with existing DB schema
    # Always set to same value as asset_symbol
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # Cash lives in PositionCell (per target state model)
    # Portfolio total cash = SUM(position.cash) - never stored at portfolio level
    cash: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anchor_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    # order policy columns (all nullable)
    op_min_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    op_min_notional: Mapped[float | None] = mapped_column(Float, nullable=True)
    op_lot_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    op_qty_step: Mapped[float | None] = mapped_column(Float, nullable=True)
    op_action_below_min: Mapped[str | None] = mapped_column(String, nullable=True)

    # guardrails columns (all nullable)
    gr_min_stock_alloc_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    gr_max_stock_alloc_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    gr_max_orders_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Commission and dividend aggregates (per spec)
    total_commission_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_dividends_received: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Status enum: RUNNING / PAUSED (per canonical model)
    # Note: This column may not exist in older databases - run migration to add it
    status: Mapped[str] = mapped_column(
        String, nullable=True, default="RUNNING", index=True
    )  # RUNNING / PAUSED - nullable=True to handle missing column gracefully

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint("status IN ('RUNNING', 'PAUSED')", name="ck_positions_status"),
    )


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    portfolio_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    position_id: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="submitted")
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    # Commission fields (per spec)
    commission_rate_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    commission_estimated: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Broker integration fields (Phase 1)
    broker_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    broker_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    submitted_to_broker_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    filled_qty: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_fill_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_commission: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_broker_update: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("position_id", "idempotency_key", name="uq_orders_pos_idempotency"),
        Index("ix_orders_tenant_portfolio", "tenant_id", "portfolio_id"),
        Index("ix_orders_position_created_at", "position_id", "created_at"),
        Index("ix_orders_broker_order_id", "broker_order_id"),
        CheckConstraint("side IN ('BUY','SELL')", name="ck_orders_side"),
        CheckConstraint(
            "status IN ('created', 'submitted', 'pending', 'working', 'partial', 'filled', 'rejected', 'cancelled')",
            name="ck_orders_status",
        ),
    )


class TradeModel(Base):
    __tablename__ = "trades"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    portfolio_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    position_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    side: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    commission: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    commission_rate_effective: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Actual rate applied
    status: Mapped[str] = mapped_column(String, nullable=False, default="executed")
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_trades_tenant_portfolio", "tenant_id", "portfolio_id"),
        Index("ix_trades_position_executed_at", "position_id", "executed_at"),
        Index("ix_trades_order_id", "order_id"),
        CheckConstraint("side IN ('BUY','SELL')", name="ck_trades_side"),
    )


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    portfolio_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    trace_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    asset_symbol: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    position_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Legacy field, kept for compatibility
    inputs: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    outputs: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    payload_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=True
    )  # New field for structured payload
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )  # Legacy field

    __table_args__ = (
        Index("ix_events_tenant_portfolio", "tenant_id", "portfolio_id"),
        Index("ix_events_trace_id", "trace_id"),
        Index("ix_events_position_ts", "position_id", "ts"),
        Index("ix_events_timestamp", "timestamp"),
    )


class PortfolioStateModel(Base):
    __tablename__ = "portfolio_states"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    initial_cash: Mapped[float] = mapped_column(Float, nullable=False)
    initial_asset_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    initial_asset_units: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_cash: Mapped[float] = mapped_column(Float, nullable=False)
    current_asset_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_asset_units: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_portfolio_states_active", "is_active"),
        Index("ix_portfolio_states_updated_at", "updated_at"),
    )


class PortfolioModel(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, default="default")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    positions: Mapped[List["PortfolioPositionModel"]] = relationship(
        "PortfolioPositionModel", back_populates="portfolio", cascade="all, delete-orphan"
    )

    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False, default="LIVE")  # LIVE/SIM/SANDBOX
    trading_state: Mapped[str] = mapped_column(
        String, nullable=False, default="NOT_CONFIGURED"
    )  # READY/RUNNING/PAUSED/ERROR/NOT_CONFIGURED
    trading_hours_policy: Mapped[str] = mapped_column(
        String, nullable=False, default="OPEN_ONLY"
    )  # OPEN_ONLY/OPEN_PLUS_AFTER_HOURS

    __table_args__ = (
        Index("ix_portfolios_tenant_id", "tenant_id"),
        Index("ix_portfolios_user_id", "user_id"),
        Index("ix_portfolios_created_at", "created_at"),
        Index("ix_portfolios_updated_at", "updated_at"),
        UniqueConstraint("tenant_id", "id", name="uq_portfolios_tenant_id"),
    )


# REMOVED: PortfolioCashModel - Cash is now stored in Position.cash


class PortfolioConfigModel(Base):
    __tablename__ = "portfolio_config"

    tenant_id: Mapped[str] = mapped_column(String, primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(String, primary_key=True)
    trigger_up_pct: Mapped[float] = mapped_column(Float, nullable=False, default=3.0)
    trigger_down_pct: Mapped[float] = mapped_column(Float, nullable=False, default=-3.0)
    min_stock_pct: Mapped[float] = mapped_column(Float, nullable=False, default=20.0)
    max_stock_pct: Mapped[float] = mapped_column(Float, nullable=False, default=80.0)
    max_trade_pct_of_position: Mapped[float | None] = mapped_column(Float, nullable=True)
    commission_rate_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "portfolio_id"],
            ["portfolios.tenant_id", "portfolios.id"],
            ondelete="CASCADE",
        ),
        Index("ix_portfolio_config_tenant_portfolio", "tenant_id", "portfolio_id"),
    )


class PositionEvaluationTimelineModel(Base):
    """
    Canonical table for all position evaluation cycles.

    One row is written for EVERY evaluation cycle, not only when trades occur.
    Used for both live trading (mode='LIVE') and simulation (mode='SIMULATION').

    All Excel exports and audit/debug UI are projections of this table.

    Design principles:
    - One row = one evaluation point
    - Chronological first (timestamp is primary ordering key)
    - Everything explainable (reason, inputs, constraints, outcome)
    - Verbose is additive (verbose view ⊇ compact view)
    - No duplicated logic (views are projections, not separate tables)
    """

    __tablename__ = "position_evaluation_timeline"

    # ========== PRIMARY KEYS & IDENTIFICATION ==========
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    portfolio_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    portfolio_name: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # Denormalized for readability
    position_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)  # Asset symbol
    exchange: Mapped[str | None] = mapped_column(String, nullable=True)  # Exchange code
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )  # Primary ordering key
    market_session: Mapped[str | None] = mapped_column(String, nullable=True)  # REGULAR / EXTENDED
    evaluation_type: Mapped[str] = mapped_column(
        String, nullable=False, default="DAILY_CHECK", index=True
    )  # DAILY_CHECK / PRICE_UPDATE / DIVIDEND / TRADE_INTENT / EXECUTION
    evaluation_seq: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Monotonic per position
    trace_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )  # Links related evaluations

    # Mode: LIVE for live trading, SIMULATION for backtesting
    mode: Mapped[str] = mapped_column(String, nullable=False, default="LIVE", index=True)
    simulation_run_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )  # For simulation mode

    # ========== MARKET DATA (Raw + Effective Pricing with Policy) ==========
    # OHLCV (if available)
    open_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    high_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Quote details (pricing source)
    last_trade_price: Mapped[float | None] = mapped_column(Float, nullable=True)  # Raw
    best_bid: Mapped[float | None] = mapped_column(Float, nullable=True)  # Raw
    best_ask: Mapped[float | None] = mapped_column(Float, nullable=True)  # Raw
    official_close_price: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Previous close
    effective_price: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Price actually used
    price_policy_requested: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # MID, LAST_TRADE, OFFICIAL_CLOSE
    price_policy_effective: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # After fallback
    price_fallback_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Why fallback occurred
    data_provider: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # yfinance, broker, etc

    # Market hours validation
    is_market_hours: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_after_hours: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    trading_hours_policy: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # OPEN_ONLY, OPEN_PLUS_AFTER_HOURS
    price_validation_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    price_validation_rejections: Mapped[List[str] | None] = mapped_column(JSON, nullable=True)
    price_validation_warnings: Mapped[List[str] | None] = mapped_column(JSON, nullable=True)

    # Data quality flags
    is_fresh: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )  # Within 3 seconds
    is_inline: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )  # Within ±1% of mid-quote

    # ========== POSITION STATE (Before Evaluation) ==========
    position_qty_before: Mapped[float] = mapped_column(Float, nullable=False)
    position_cash_before: Mapped[float] = mapped_column(Float, nullable=False)
    position_stock_value_before: Mapped[float] = mapped_column(Float, nullable=False)  # qty * price
    position_total_value_before: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # cash + stock
    position_stock_pct_before: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # stock / total
    position_dividend_receivable_before: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    # Cash and stock percentages
    cash_pct: Mapped[float | None] = mapped_column(Float, nullable=True)  # cash / total
    stock_pct: Mapped[float | None] = mapped_column(Float, nullable=True)  # stock / total

    # ========== DIVIDEND DATA (if applicable) ==========
    dividend_declared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dividend_ex_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dividend_pay_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dividend_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # Per share
    dividend_gross_value: Mapped[float | None] = mapped_column(Float, nullable=True)  # qty × rate
    dividend_tax: Mapped[float | None] = mapped_column(Float, nullable=True)  # Withholding
    dividend_net_value: Mapped[float | None] = mapped_column(Float, nullable=True)  # Cash added
    dividend_applied: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # Applied this row

    # ========== STRATEGY STATE (Anchor, Triggers, Guardrails) ==========
    # Anchor & deltas
    anchor_price: Mapped[float | None] = mapped_column(Float, nullable=True)  # Current anchor
    pct_change_from_anchor: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # (price-anchor)/anchor
    pct_change_from_prev: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Price delta vs last row
    anchor_updated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anchor_reset_old_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    anchor_reset_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Trigger configuration & evaluation
    trigger_up_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)  # %
    trigger_down_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)  # %
    trigger_direction: Mapped[str | None] = mapped_column(String, nullable=True)  # UP / DOWN / NONE
    trigger_fired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    trigger_reason: Mapped[str | None] = mapped_column(Text, nullable=True)  # Human-readable

    # Guardrail configuration & evaluation
    guardrail_min_stock_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    guardrail_max_stock_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    guardrail_max_trade_pct: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # max_trade_pct_of_position
    guardrail_max_orders_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    guardrail_allowed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    guardrail_block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)  # Why blocked

    # Order policy configuration
    order_policy_rebalance_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    order_policy_commission_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    order_policy_min_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    order_policy_min_notional: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ========== ACTION DECISION ==========
    action: Mapped[str] = mapped_column(
        String, nullable=False, default="HOLD"
    )  # BUY, SELL, HOLD, SKIP
    action_reason: Mapped[str | None] = mapped_column(Text, nullable=True)  # Full explanation
    trade_intent_qty: Mapped[float | None] = mapped_column(Float, nullable=True)  # Intended shares
    trade_intent_value: Mapped[float | None] = mapped_column(Float, nullable=True)  # Intended value
    trade_intent_cash_delta: Mapped[float | None] = mapped_column(Float, nullable=True)  # ±cash

    # Legacy fields (for backward compatibility)
    action_taken: Mapped[str] = mapped_column(
        String, nullable=False, default="HOLD"
    )  # Maps to action
    action_side: Mapped[str | None] = mapped_column(String, nullable=True)  # BUY, SELL
    action_qty_raw: Mapped[float | None] = mapped_column(Float, nullable=True)  # Before trimming
    action_qty_trimmed: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # After guardrail trimming
    action_notional: Mapped[float | None] = mapped_column(Float, nullable=True)
    action_commission_estimated: Mapped[float | None] = mapped_column(Float, nullable=True)
    action_trimming_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_allowed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    decision_rejections: Mapped[List[str] | None] = mapped_column(JSON, nullable=True)
    decision_warnings: Mapped[List[str] | None] = mapped_column(JSON, nullable=True)
    decision_explanation: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Verbose explanation

    # Post-trade projection (if action would be taken)
    post_trade_stock_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    post_trade_stock_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    post_trade_cash: Mapped[float | None] = mapped_column(Float, nullable=True)
    post_trade_total_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ========== EXECUTION RESULT (If Any) ==========
    order_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    trade_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    execution_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    execution_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    execution_commission: Mapped[float | None] = mapped_column(Float, nullable=True)
    execution_commission_rate_effective: Mapped[float | None] = mapped_column(Float, nullable=True)
    execution_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    execution_status: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # FILLED, PARTIAL, EXPIRED, NONE
    commission_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # Snapshot
    commission_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ========== POSITION STATE (After Evaluation/Execution) ==========
    position_qty_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_cash_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_stock_value_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_total_value_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_stock_pct_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_anchor_price: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # If anchor was updated

    # ========== DERIVED PORTFOLIO IMPACT ==========
    portfolio_total_value_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    portfolio_total_value_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    portfolio_cash_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    portfolio_cash_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    portfolio_stock_value_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    portfolio_stock_value_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_weight_pct_before: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # position / portfolio total
    position_weight_pct_after: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ========== VERBOSE EXPLANATION FIELDS (for debug mode) ==========
    evaluation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Free-form
    pricing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Why this price
    trigger_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Math explanation
    guardrail_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Why allowed/blocked
    action_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Why this action
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)  # Liquidity, fallback, etc

    # Legacy verbose fields (for backward compatibility)
    evaluation_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # High-level summary
    evaluation_details: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Full evaluation details
    market_data_details: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Full market data
    strategy_state_details: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Full strategy config
    execution_details: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Full execution details

    # Source of evaluation (worker, api/manual, simulation)
    source: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    __table_args__ = (
        # Primary ordering: timestamp (chronological first)
        Index("ix_eval_timeline_timestamp", "timestamp"),
        Index("ix_eval_timeline_tenant_portfolio", "tenant_id", "portfolio_id"),
        Index(
            "ix_eval_timeline_position_timestamp", "position_id", "timestamp"
        ),  # Per-position chronological
        Index(
            "ix_eval_timeline_symbol_timestamp", "symbol", "timestamp"
        ),  # Per-symbol chronological
        Index("ix_eval_timeline_trace_id", "trace_id"),
        Index("ix_eval_timeline_mode", "mode"),
        Index("ix_eval_timeline_simulation_run", "simulation_run_id"),
        Index("ix_eval_timeline_action", "action"),  # For action-only view
        Index("ix_eval_timeline_dividend_applied", "dividend_applied"),  # For dividends view
        # Composite indexes for common queries
        Index("ix_eval_timeline_portfolio_timestamp", "portfolio_id", "timestamp"),
        Index("ix_eval_timeline_position_seq", "position_id", "evaluation_seq"),
        CheckConstraint("mode IN ('LIVE', 'SIMULATION')", name="ck_eval_timeline_mode"),
        CheckConstraint(
            "action IN ('BUY', 'SELL', 'HOLD', 'SKIP')", name="ck_eval_timeline_action"
        ),
        CheckConstraint(
            "market_session IN ('REGULAR', 'EXTENDED', NULL)", name="ck_eval_timeline_session"
        ),
        CheckConstraint(
            "trigger_direction IN ('UP', 'DOWN', 'NONE', NULL)", name="ck_eval_timeline_trigger_dir"
        ),
        CheckConstraint(
            "evaluation_type IN ('DAILY_CHECK', 'PRICE_UPDATE', 'DIVIDEND', 'TRADE_INTENT', 'EXECUTION')",
            name="ck_eval_timeline_evaluation_type",
        ),
    )


class PortfolioPositionModel(Base):
    __tablename__ = "portfolio_positions"

    portfolio_id: Mapped[str] = mapped_column(
        String, ForeignKey("portfolios.id", ondelete="CASCADE"), primary_key=True
    )
    position_id: Mapped[str] = mapped_column(
        String, ForeignKey("positions.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    portfolio: Mapped["PortfolioModel"] = relationship("PortfolioModel", back_populates="positions")

    __table_args__ = (
        Index("ix_portfolio_positions_portfolio_id", "portfolio_id"),
        Index("ix_portfolio_positions_position_id", "position_id"),
        UniqueConstraint("portfolio_id", "position_id", name="uq_portfolio_positions"),
    )


def get_engine(url: str) -> Engine:
    # SQLite-specific configuration for better concurrency handling
    if url.startswith("sqlite"):
        return create_engine(
            url,
            future=True,
            pool_pre_ping=True,
            pool_size=1,  # Single connection for SQLite
            connect_args={
                "check_same_thread": False,
                "timeout": 30,
                "isolation_level": None,  # Autocommit mode
            },
        )
    else:
        return create_engine(url, future=True)


def create_all(engine: Engine) -> None:
    """Create all tables and indexes, ignoring existing ones."""
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        # If there are index conflicts, try to create tables without indexes first
        if "already exists" in str(e).lower():
            print(
                "Warning: Some database objects already exist. Attempting to create missing tables only..."
            )
            # Create tables without indexes first
            for table in Base.metadata.tables.values():
                try:
                    table.create(engine, checkfirst=True)
                except Exception as table_error:
                    if "already exists" not in str(table_error).lower():
                        print(f"Warning: Could not create table {table.name}: {table_error}")

            # Then try to create indexes individually
            for table in Base.metadata.tables.values():
                for index in table.indexes:
                    try:
                        index.create(engine, checkfirst=True)
                    except Exception as index_error:
                        if "already exists" not in str(index_error).lower():
                            print(f"Warning: Could not create index {index.name}: {index_error}")
        else:
            raise e


# Optimization System Models


class OptimizationConfigModel(Base):
    __tablename__ = "optimization_configs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    parameter_ranges: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    optimization_criteria: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    max_combinations: Mapped[int] = mapped_column(Integer, nullable=True)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    results: Mapped[List["OptimizationResultModel"]] = relationship(
        "OptimizationResultModel", back_populates="config", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_optimization_configs_created_by", "created_by"),
        Index("ix_optimization_configs_status", "status"),
        Index("ix_optimization_configs_created_at", "created_at"),
        CheckConstraint(
            "status IN ('draft', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_optimization_configs_status",
        ),
    )


class OptimizationResultModel(Base):
    __tablename__ = "optimization_results"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    config_id: Mapped[str] = mapped_column(
        String, ForeignKey("optimization_configs.id"), nullable=False
    )
    parameter_combination: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    combination_id: Mapped[str] = mapped_column(String, nullable=False)
    metrics: Mapped[Dict[str, float]] = mapped_column(JSON, nullable=False)
    simulation_result: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    execution_time_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    config: Mapped["OptimizationConfigModel"] = relationship(
        "OptimizationConfigModel", back_populates="results"
    )

    __table_args__ = (
        Index("ix_optimization_results_config_id", "config_id"),
        Index("ix_optimization_results_status", "status"),
        Index("ix_optimization_results_created_at", "created_at"),
        Index("ix_optimization_results_combination_id", "combination_id"),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_optimization_results_status",
        ),
    )


class HeatmapDataModel(Base):
    __tablename__ = "heatmap_data"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    config_id: Mapped[str] = mapped_column(
        String, ForeignKey("optimization_configs.id"), nullable=False
    )
    x_parameter: Mapped[str] = mapped_column(String, nullable=False)
    y_parameter: Mapped[str] = mapped_column(String, nullable=False)
    metric: Mapped[str] = mapped_column(String, nullable=False)
    heatmap_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    config: Mapped["OptimizationConfigModel"] = relationship("OptimizationConfigModel")

    __table_args__ = (
        Index("ix_heatmap_data_config_id", "config_id"),
        Index("ix_heatmap_data_parameters", "x_parameter", "y_parameter"),
        Index("ix_heatmap_data_metric", "metric"),
        Index("ix_heatmap_data_created_at", "created_at"),
    )


class SimulationResultModel(Base):
    __tablename__ = "simulation_results"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_trading_days: Mapped[int] = mapped_column(Integer, nullable=False)
    initial_cash: Mapped[float] = mapped_column(Float, nullable=False)

    # Algorithm performance
    algorithm_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    algorithm_pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    algorithm_return_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    algorithm_volatility: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    algorithm_sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    algorithm_max_drawdown: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Buy & Hold performance
    buy_hold_pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    buy_hold_return_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    buy_hold_volatility: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    buy_hold_sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    buy_hold_max_drawdown: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Comparison metrics
    excess_return: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    alpha: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    beta: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    information_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Detailed data (stored as JSON)
    trade_log: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    daily_returns: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    dividend_analysis: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    price_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    trigger_analysis: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    time_series_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    debug_info: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_simulation_results_ticker", "ticker"),
        Index("ix_simulation_results_start_date", "start_date"),
        Index("ix_simulation_results_end_date", "end_date"),
        Index("ix_simulation_results_created_at", "created_at"),
    )


class CommissionRateModel(Base):
    """SQL model for commission rate configuration."""

    __tablename__ = "commission_rates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scope: Mapped[str] = mapped_column(String, nullable=False)  # GLOBAL, TENANT, TENANT_ASSET
    tenant_id: Mapped[str | None] = mapped_column(String, nullable=True)
    asset_id: Mapped[str | None] = mapped_column(String, nullable=True)
    rate: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("scope", "tenant_id", "asset_id", name="uq_commission_rates_scope"),
        Index("ix_commission_rates_scope", "scope", "tenant_id", "asset_id"),
    )


class TriggerConfigModel(Base):
    """SQL model for trigger configuration."""

    __tablename__ = "trigger_configs"

    position_id: Mapped[str] = mapped_column(String, primary_key=True)
    up_threshold_pct: Mapped[float] = mapped_column(Float, nullable=False)
    down_threshold_pct: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class GuardrailConfigModel(Base):
    """SQL model for guardrail configuration."""

    __tablename__ = "guardrail_configs"

    position_id: Mapped[str] = mapped_column(String, primary_key=True)
    min_stock_pct: Mapped[float] = mapped_column(Float, nullable=False)
    max_stock_pct: Mapped[float] = mapped_column(Float, nullable=False)
    max_trade_pct_of_position: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_daily_notional: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_orders_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class OrderPolicyConfigModel(Base):
    """SQL model for order policy configuration."""

    __tablename__ = "order_policy_configs"

    position_id: Mapped[str] = mapped_column(String, primary_key=True)
    min_qty: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    min_notional: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    lot_size: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    qty_step: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    action_below_min: Mapped[str] = mapped_column(String, nullable=False, default="hold")
    rebalance_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=1.6667)
    order_sizing_strategy: Mapped[str] = mapped_column(
        String, nullable=False, default="proportional"
    )
    allow_after_hours: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    commission_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class PositionBaselineModel(Base):
    """
    Canonical PositionBaseline table.

    Stores baseline snapshots for positions to track performance over time.
    """

    __tablename__ = "position_baselines"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    position_id: Mapped[str] = mapped_column(String, nullable=False, index=True)  # FK to positions
    baseline_price: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_qty: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_cash: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_total_value: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_stock_value: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    __table_args__ = (
        Index("ix_position_baselines_position_timestamp", "position_id", "baseline_timestamp"),
    )


class PositionEventModel(Base):
    """
    Canonical PositionEvent table (immutable log).

    Simplified immutable log of position events. This is a compact view
    of PositionEvaluationTimeline for quick queries and audit trails.
    """

    __tablename__ = "position_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    position_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )  # PRICE / TRIGGER / GUARDRAIL / ORDER / TRADE
    effective_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False, default="NONE")  # BUY / SELL / NONE
    action_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    qty_before: Mapped[float] = mapped_column(Float, nullable=False)
    qty_after: Mapped[float] = mapped_column(Float, nullable=False)
    cash_before: Mapped[float] = mapped_column(Float, nullable=False)
    cash_after: Mapped[float] = mapped_column(Float, nullable=False)
    total_value_after: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        Index("ix_position_events_position_timestamp", "position_id", "timestamp"),
        Index("ix_position_events_event_type", "event_type"),
        CheckConstraint(
            "event_type IN ('PRICE', 'TRIGGER', 'GUARDRAIL', 'ORDER', 'TRADE')",
            name="ck_position_events_event_type",
        ),
        CheckConstraint("action IN ('BUY', 'SELL', 'NONE')", name="ck_position_events_action"),
    )

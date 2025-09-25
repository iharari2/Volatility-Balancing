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
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PositionModel(Base):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cash: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anchor_price: Mapped[float | None] = mapped_column(Float, nullable=True)

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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    position_id: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="submitted")
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("position_id", "idempotency_key", name="uq_orders_pos_idempotency"),
        Index("ix_orders_position_created_at", "position_id", "created_at"),
        CheckConstraint("side IN ('BUY','SELL')", name="ck_orders_side"),
    )


class TradeModel(Base):
    __tablename__ = "trades"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    position_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    side: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    commission: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_trades_position_executed_at", "position_id", "executed_at"),
        Index("ix_trades_order_id", "order_id"),
        CheckConstraint("side IN ('BUY','SELL')", name="ck_trades_side"),
    )


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    position_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    inputs: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    outputs: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (Index("ix_events_position_ts", "position_id", "ts"),)


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


def get_engine(url: str) -> Engine:
    # SQLite-specific configuration for better concurrency handling
    if url.startswith("sqlite"):
        return create_engine(
            url,
            future=True,
            pool_pre_ping=True,
            pool_size=1,  # Single connection for SQLite
            max_overflow=0,  # No overflow connections
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

# backend/infrastructure/persistence/sql/models.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

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
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PositionModel(Base):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cash: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

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


def get_engine(url: str) -> Engine:
    return create_engine(url, future=True)


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(engine)

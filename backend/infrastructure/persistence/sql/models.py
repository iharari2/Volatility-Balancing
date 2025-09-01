# =========================
# backend/infrastructure/persistence/sql/models.py
# =========================
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Float,
    DateTime,
    UniqueConstraint,
    create_engine,
    JSON,
    Index,
    Text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import CheckConstraint


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
    op_min_notional: Mapped[float] = mapped_column(Float, nullable=True)
    op_lot_size: Mapped[float] = mapped_column(Float, nullable=True)
    op_qty_step: Mapped[float] = mapped_column(Float, nullable=True)
    op_action_below_min: Mapped[str | None] = mapped_column(String, nullable=True)

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
        CheckConstraint("side IN ('BUY','SELL')", name="ck_orders_side"),  # optional but nice
    )


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    position_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    outputs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (Index("ix_events_position_ts", "position_id", "ts"),)


def get_engine(url: str) -> Engine:
    return create_engine(url, future=True)


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(engine)

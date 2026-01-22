# =========================
# backend/infrastructure/persistence/sql/orders_repo_sql.py
# =========================
from __future__ import annotations

from datetime import datetime, timezone, time, date
from typing import Optional, Iterable, List, cast

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, sessionmaker

from domain.entities.order import Order
from domain.ports.orders_repo import OrdersRepo
from domain.value_objects.types import OrderSide, OrderStatus
from .models import OrderModel

__all__ = ["SQLOrdersRepo"]


class SQLOrdersRepo(OrdersRepo):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def count_for_position_between(self, position_id: str, start: datetime, end: datetime) -> int:
        with self._sf() as s:
            stmt = select(func.count(OrderModel.id)).where(
                OrderModel.position_id == position_id,
                OrderModel.created_at >= start,
                OrderModel.created_at < end,
                OrderModel.status.in_(("submitted", "filled", "rejected")),
            )
            return int(s.scalar(stmt) or 0)

    def create(
        self,
        *,
        tenant_id: str,
        portfolio_id: str,
        position_id: str,
        side: OrderSide,
        qty: float,
        idempotency_key: str,
    ) -> str:
        """Create a submitted order and return its generated ID."""
        from uuid import uuid4

        order_id = f"ord_{uuid4().hex[:8]}"
        order = Order(
            id=order_id,
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            side=side,
            qty=qty,
            status="submitted",
            idempotency_key=idempotency_key,
        )
        self.save(order)
        return order_id

    def get(self, order_id: str) -> Optional[Order]:
        with self._sf() as s:
            row = s.get(OrderModel, order_id)
            if not row:
                return None
            return Order(
                id=row.id,
                tenant_id=row.tenant_id,
                portfolio_id=row.portfolio_id,
                position_id=row.position_id,
                side=cast(OrderSide, row.side),
                qty=row.qty,
                status=cast(OrderStatus, row.status),
                idempotency_key=row.idempotency_key,
                commission_rate_snapshot=getattr(row, "commission_rate_snapshot", None),
                commission_estimated=getattr(row, "commission_estimated", None),
                created_at=row.created_at,
                updated_at=row.updated_at,
                # Broker integration fields
                broker_order_id=getattr(row, "broker_order_id", None),
                broker_status=getattr(row, "broker_status", None),
                submitted_to_broker_at=getattr(row, "submitted_to_broker_at", None),
                filled_qty=getattr(row, "filled_qty", 0.0) or 0.0,
                avg_fill_price=getattr(row, "avg_fill_price", None),
                total_commission=getattr(row, "total_commission", 0.0) or 0.0,
                last_broker_update=getattr(row, "last_broker_update", None),
                rejection_reason=getattr(row, "rejection_reason", None),
            )

    def save(self, order: Order) -> None:
        with self._sf() as s:
            obj = s.get(OrderModel, order.id)
            if obj is None:
                s.add(
                    OrderModel(
                        id=order.id,
                        tenant_id=order.tenant_id,
                        portfolio_id=order.portfolio_id,
                        position_id=order.position_id,
                        side=order.side,
                        qty=order.qty,
                        status=order.status,
                        idempotency_key=order.idempotency_key,
                        commission_rate_snapshot=order.commission_rate_snapshot,
                        commission_estimated=order.commission_estimated,
                        created_at=order.created_at,
                        updated_at=order.updated_at,
                        # Broker integration fields
                        broker_order_id=order.broker_order_id,
                        broker_status=order.broker_status,
                        submitted_to_broker_at=order.submitted_to_broker_at,
                        filled_qty=order.filled_qty,
                        avg_fill_price=order.avg_fill_price,
                        total_commission=order.total_commission,
                        last_broker_update=order.last_broker_update,
                        rejection_reason=order.rejection_reason,
                    )
                )
            else:
                obj.tenant_id = order.tenant_id
                obj.portfolio_id = order.portfolio_id
                obj.position_id = order.position_id
                obj.side = order.side
                obj.qty = order.qty
                obj.status = order.status
                obj.idempotency_key = order.idempotency_key or ""
                obj.commission_rate_snapshot = order.commission_rate_snapshot
                obj.commission_estimated = order.commission_estimated
                obj.updated_at = order.updated_at
                # Broker integration fields
                obj.broker_order_id = order.broker_order_id
                obj.broker_status = order.broker_status
                obj.submitted_to_broker_at = order.submitted_to_broker_at
                obj.filled_qty = order.filled_qty
                obj.avg_fill_price = order.avg_fill_price
                obj.total_commission = order.total_commission
                obj.last_broker_update = order.last_broker_update
                obj.rejection_reason = order.rejection_reason
            s.commit()

    def count_for_position_on_day(self, position_id: str, day: date) -> int:
        start = datetime.combine(day, time.min).replace(tzinfo=timezone.utc)
        end = datetime.combine(day, time.max).replace(tzinfo=timezone.utc)
        with self._sf() as s:
            return int(
                s.query(func.count(OrderModel.id))
                .filter(OrderModel.position_id == position_id)
                .filter(OrderModel.created_at >= start)
                .filter(OrderModel.created_at <= end)
                .scalar()
                or 0
            )

    def clear(self) -> None:
        with self._sf() as s:
            s.query(OrderModel).delete()
            s.commit()

    def list_for_position(self, position_id: str, limit: int = 100) -> Iterable[Order]:
        with self._sf() as s:
            rows: List[OrderModel] = (
                s.query(OrderModel)
                .filter(OrderModel.position_id == position_id)
                .order_by(desc(OrderModel.created_at))
                .limit(limit)
                .all()
            )
            return [
                Order(
                    id=r.id,
                    tenant_id=r.tenant_id,
                    portfolio_id=r.portfolio_id,
                    position_id=r.position_id,
                    side=cast(OrderSide, r.side),
                    qty=r.qty,
                    status=cast(OrderStatus, r.status),
                    idempotency_key=r.idempotency_key,
                    commission_rate_snapshot=getattr(r, "commission_rate_snapshot", None),
                    commission_estimated=getattr(r, "commission_estimated", None),
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                    # Broker integration fields
                    broker_order_id=getattr(r, "broker_order_id", None),
                    broker_status=getattr(r, "broker_status", None),
                    submitted_to_broker_at=getattr(r, "submitted_to_broker_at", None),
                    filled_qty=getattr(r, "filled_qty", 0.0) or 0.0,
                    avg_fill_price=getattr(r, "avg_fill_price", None),
                    total_commission=getattr(r, "total_commission", 0.0) or 0.0,
                    last_broker_update=getattr(r, "last_broker_update", None),
                    rejection_reason=getattr(r, "rejection_reason", None),
                )
                for r in rows
            ]

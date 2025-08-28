# =========================
# /backend/infrastructure/persistence/sql/orders_repo_sql.py
# =========================
from __future__ import annotations
from datetime import datetime, timezone, time
from typing import Optional, cast
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

from domain.entities.order import Order, OrderSide, OrderStatus
from domain.ports.orders_repo import OrdersRepo
from .models import OrderModel


__all__ = ["SQLOrdersRepo"]  # <- explicit export


class SQLOrdersRepo(OrdersRepo):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def get(self, order_id: str) -> Optional[Order]:
        with self._sf() as s:
            row = s.get(OrderModel, order_id)
            if not row:
                return None
            return Order(
                id=row.id,
                position_id=row.position_id,
                side=cast(OrderSide, row.side),
                qty=row.qty,
                status=cast(OrderStatus, row.status),
                idempotency_key=row.idempotency_key,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    def save(self, order: Order) -> None:
        with self._sf() as s:
            obj = s.get(OrderModel, order.id)
            if obj is None:
                s.add(
                    OrderModel(
                        id=order.id,
                        position_id=order.position_id,
                        side=order.side,
                        qty=order.qty,
                        status=order.status,
                        idempotency_key=order.idempotency_key,
                        created_at=order.created_at,
                        updated_at=order.updated_at,
                    )
                )
            else:
                obj.position_id = order.position_id
                obj.side = order.side
                obj.qty = order.qty
                obj.status = order.status
                obj.idempotency_key = order.idempotency_key
                obj.updated_at = order.updated_at
            s.commit()

    def count_for_position_on_day(self, position_id: str, day) -> int:
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

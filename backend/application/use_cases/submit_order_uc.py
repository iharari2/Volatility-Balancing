# backend/application/use_cases/submit_order_uc.py
from __future__ import annotations

import hashlib
import uuid
from typing import Any, Dict

from application.dto.orders import CreateOrderRequest, CreateOrderResponse
from domain.entities.order import Order
from domain.entities.event import Event
from domain.errors import IdempotencyConflict
from domain.ports.events_repo import EventsRepo
from domain.ports.idempotency_repo import IdempotencyRepo
from domain.ports.orders_repo import OrdersRepo
from domain.ports.positions_repo import PositionsRepo
from infrastructure.time.clock import Clock


class SubmitOrderUC:
    """Idempotent order submission flow that returns a CreateOrderResponse."""

    def __init__(
        self,
        positions: PositionsRepo,
        orders: OrdersRepo,
        idempotency: IdempotencyRepo,
        events: EventsRepo,
        clock: Clock,
    ) -> None:
        self.positions = positions
        self.orders = orders
        self.idempotency = idempotency
        self.events = events
        self.clock = clock

    @staticmethod
    def _signature(position_id: str, req: CreateOrderRequest) -> str:
        payload: Dict[str, Any] = {"position_id": position_id, "side": req.side, "qty": req.qty}
        raw = str(sorted(payload.items())).encode()
        return hashlib.sha256(raw).hexdigest()

    def execute(
        self, position_id: str, request: CreateOrderRequest, idempotency_key: str
    ) -> CreateOrderResponse:
        # 1) Validate position
        pos = self.positions.get(position_id)
        if not pos:
            raise KeyError("position_not_found")

        # 2) Signature + per-position scoped key
        sig = self._signature(position_id, request)
        scoped_key = f"{position_id}:{idempotency_key}"

        # Try to reserve idempotency key; the repo should return:
        # - None if reserved OK
        # - existing order_id if same signature was already processed
        # - a string starting with "conflict:" if same key but different signature
        existing = self.idempotency.reserve(scoped_key, sig)
        if isinstance(existing, str):
            if existing.startswith("conflict:"):
                raise IdempotencyConflict("idempotency_signature_mismatch")
            # existing is an order_id for the same signature → return same response
            return CreateOrderResponse(order_id=existing, accepted=True, position_id=position_id)

        # 3) Daily cap guardrail
        today = self.clock.now().date()
        if (
            self.orders.count_for_position_on_day(position_id, today)
            >= pos.guardrails.max_orders_per_day
        ):
            from domain.errors import GuardrailBreach

            raise GuardrailBreach("daily_order_cap_exceeded")

        # 4) Create order
        order_id = f"ord_{uuid.uuid4().hex[:8]}"
        order = Order(
            id=order_id,
            position_id=position_id,
            side=request.side,
            qty=request.qty,
            status="submitted",
            idempotency_key=idempotency_key,
            request_signature={
                "position_id": position_id,
                "side": request.side,
                "qty": request.qty,
            },
        )
        self.orders.save(order)

        # Finalize idempotency outcome
        self.idempotency.put(scoped_key, order_id, sig)

        # 5) Event
        evt = Event(
            id=f"evt_{order_id}",
            position_id=position_id,
            type="order_submitted",
            inputs={"side": request.side, "qty": request.qty},
            outputs={"order_id": order_id},
            message=f"order submitted ({request.side} {request.qty})",
            ts=self.clock.now(),
        )
        self.events.append(evt)

        return CreateOrderResponse(order_id=order_id, accepted=True, position_id=position_id)

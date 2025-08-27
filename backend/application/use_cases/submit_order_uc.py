# =========================
# backend/application/use_cases/submit_order_uc.py
# =========================
import hashlib
import uuid
from dataclasses import asdict
from datetime import date
from typing import Dict, Any, Tuple

from application.dto.orders import CreateOrderRequest, CreateOrderResponse
from domain.entities.order import Order
from domain.entities.event import Event
from domain.ports.positions_repo import PositionsRepo
from domain.ports.orders_repo import OrdersRepo
from domain.ports.idempotency_repo import IdempotencyRepo
from domain.ports.events_repo import EventsRepo
from domain.errors import IdempotencyConflict


class SubmitOrderUC:
    """Flow A: Idempotent order submission.
    Returns (CreateOrderResponse, replay: bool)
    """

    def __init__(self, positions: PositionsRepo, orders: OrdersRepo, idempotency: IdempotencyRepo, events: EventsRepo, clock) -> None:
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

    def execute(self, position_id: str, request: CreateOrderRequest, idempotency_key: str) -> Tuple[CreateOrderResponse, bool]:
        # 1) Check position
        pos = self.positions.get(position_id)
        if not pos:
            raise KeyError("position_not_found")

        # 2) Signature + idempotency
        sig = self._signature(position_id, request)
        existing = self.idempotency.reserve(idempotency_key, sig)
        if existing is not None:
            # If reserved for another signature, signal conflict
            if existing.startswith("conflict:"):
                raise IdempotencyConflict("idempotency_signature_mismatch")
            # Replay path
            return CreateOrderResponse(order_id=existing, accepted=True, position_id=position_id), True

        # 3) Daily cap (simple count)
        today = self.clock.now().date()
        if self.orders.count_for_position_on_day(position_id, today) >= pos.guardrails.max_orders_per_day:
            # Release not implemented in-memory; in real impl, release reservation here
            raise IdempotencyConflict("daily_order_cap_exceeded")

        # 4) Create order
        order_id = f"ord_{uuid.uuid4().hex[:8]}"
        order = Order(
            id=order_id,
            position_id=position_id,
            side=request.side,
            qty=request.qty,
            status="submitted",
            idempotency_key=idempotency_key,
            request_signature={"position_id": position_id, "side": request.side, "qty": request.qty},
        )
        self.orders.save(order)
        self.idempotency.put(idempotency_key, order_id, sig)

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

        return CreateOrderResponse(order_id=order_id, accepted=True, position_id=position_id), False


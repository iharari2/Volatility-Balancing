# backend/application/use_cases/execute_order_uc.py
from __future__ import annotations

from typing import Optional
from uuid import uuid4

from application.dto.orders import FillOrderRequest, FillOrderResponse
from domain.entities.event import Event
from domain.ports.positions_repo import PositionsRepo
from domain.ports.orders_repo import OrdersRepo
from domain.ports.events_repo import EventsRepo
from infrastructure.time.clock import Clock
from domain.errors import GuardrailBreach  # NEW


class ExecuteOrderUC:
    def __init__(
        self,
        positions: PositionsRepo,
        orders: OrdersRepo,
        events: EventsRepo,
        clock: Optional[Clock] = None,
    ) -> None:
        self.positions = positions
        self.orders = orders
        self.events = events
        self.clock = clock or Clock()

    def execute(self, order_id: str, request: FillOrderRequest) -> FillOrderResponse:
        order = self.orders.get(order_id)
        if not order:
            raise KeyError("order_not_found")

        pos = self.positions.get(order.position_id)
        if not pos:
            raise KeyError("position_not_found")

        policy = pos.order_policy
        q_req = abs(request.qty)
        q_req = policy.round_qty(q_req)
        q_req = policy.clamp_to_lot(q_req)
        commission = getattr(request, "commission", 0.0) or 0.0

        notional = q_req * request.price
        below_min = (policy.min_qty > 0 and q_req < policy.min_qty) or (
            policy.min_notional > 0 and notional < policy.min_notional
        )

        now = self.clock.now()
        uid = uuid4().hex[:8]  # NEW: short unique suffix for event IDs

        if below_min:
            if policy.action_below_min == "reject":
                order.status = "rejected"
                self.orders.save(order)
                self.events.append(
                    Event(
                        id=f"evt_reject_{order.id}_{uid}",  # NEW: unique
                        position_id=order.position_id,
                        type="fill_rejected_below_min",
                        inputs={"qty": q_req, "price": request.price},
                        outputs={"order_id": order.id},
                        ts=now,
                        message="fill rejected: below minimum order policy",
                    )
                )
                return FillOrderResponse(order_id=order.id, status="rejected", filled_qty=0.0)
            else:
                # "hold"
                self.events.append(
                    Event(
                        id=f"evt_skip_{order.id}_{uid}",  # NEW: unique
                        position_id=order.position_id,
                        type="fill_skipped_below_min",
                        inputs={"qty": q_req, "price": request.price},
                        outputs={"order_id": order.id},
                        ts=now,
                        message="fill skipped: below minimum order policy",
                    )
                )
                return FillOrderResponse(order_id=order.id, status="skipped", filled_qty=0.0)

        # NEW: SELL guardrail — reject if not enough qty BEFORE any 'filled' event
        if order.side == "SELL" and q_req > pos.qty:
            self.events.append(
                Event(
                    id=f"evt_reject_{order.id}_{uid}",
                    position_id=order.position_id,
                    type="fill_rejected_insufficient_qty",
                    inputs={"qty": q_req, "price": request.price},
                    outputs={"order_id": order.id},
                    ts=now,
                    message="insufficient position qty",
                )
            )
            raise GuardrailBreach("insufficient_qty")

        # Apply fill
        if order.side == "BUY":
            pos.qty += q_req
            pos.cash -= (q_req * request.price) + commission
        else:
            # SELL
            pos.qty -= q_req
            pos.cash += (q_req * request.price) - commission

        self.positions.save(pos)
        order.status = "filled"
        self.orders.save(order)

        self.events.append(
            Event(
                id=f"evt_filled_{order.id}_{uid}",  # NEW: unique
                position_id=order.position_id,
                type="order_filled",
                inputs={"qty": q_req, "price": request.price},
                outputs={"order_id": order.id},
                ts=now,
                message=f"order filled ({order.side} {q_req})",
            )
        )

        return FillOrderResponse(order_id=order.id, status="filled", filled_qty=q_req)

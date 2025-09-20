# backend/application/use_cases/execute_order_uc.py
from __future__ import annotations

from typing import Optional
from uuid import uuid4

from application.dto.orders import FillOrderRequest, FillOrderResponse
from domain.entities.event import Event
from domain.errors import GuardrailBreach
from domain.ports.events_repo import EventsRepo
from domain.ports.orders_repo import OrdersRepo
from domain.ports.positions_repo import PositionsRepo
from domain.ports.trades_repo import TradesRepo
from infrastructure.time.clock import Clock


class ExecuteOrderUC:
    """
    Applies an executed fill to a Position and emits events.

    Notes
    -----
    * Commission is taken from FillOrderRequest (default 0.0 if omitted).
    * "Below-min" order policy (min_qty / min_notional) is evaluated first.
      - action_below_min == "reject": order is marked rejected and an event is added.
      - action_below_min == "hold":   no position change; a 'skipped' event is added.
    * SELL guardrail: reject if requested fill exceeds current position qty.
    * After-fill guardrails: uses pos.guardrails.check_after_fill(...) to validate
      resulting cash/qty, etc. If invalid -> GuardrailBreach + event.
    * On success: updates position, marks order filled, appends 'order_filled' event.
    """

    def __init__(
        self,
        positions: PositionsRepo,
        orders: OrdersRepo,
        trades: TradesRepo,
        events: EventsRepo,
        clock: Optional[Clock] = None,
    ) -> None:
        self.positions = positions
        self.orders = orders
        self.trades = trades
        self.events = events
        self.clock = clock or Clock()

    def execute(self, order_id: str, request: FillOrderRequest) -> FillOrderResponse:
        order = self.orders.get(order_id)
        if not order:
            raise KeyError("order_not_found")

        pos = self.positions.get(order.position_id)
        if not pos:
            raise KeyError("position_not_found")

        # Normalize/round qty by order policy
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
        uid = uuid4().hex[:8]  # unique suffix for event IDs

        # Below-min policy
        if below_min:
            if policy.action_below_min == "reject":
                order.status = "rejected"
                self.orders.save(order)
                self.events.append(
                    Event(
                        id=f"evt_reject_{order.id}_{uid}",
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
                        id=f"evt_skip_{order.id}_{uid}",
                        position_id=order.position_id,
                        type="fill_skipped_below_min",
                        inputs={"qty": q_req, "price": request.price},
                        outputs={"order_id": order.id},
                        ts=now,
                        message="fill skipped: below minimum order policy",
                    )
                )
                return FillOrderResponse(order_id=order.id, status="skipped", filled_qty=0.0)

        # SELL guardrail: insufficient qty before applying any changes
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

        # Validate after-fill guardrails (cash/qty allocation, etc.)
        ok, why = pos.guardrails.check_after_fill(
            qty_now=pos.qty,
            cash_now=pos.cash,
            side=order.side,
            fill_qty=q_req,
            price=request.price,
            commission=commission,
            dividend_receivable=pos.dividend_receivable,
        )
        if not ok:
            self.events.append(
                Event(
                    id=f"evt_gr_{order.id}_{uid}",
                    position_id=order.position_id,
                    type="guardrail_breach",
                    inputs={
                        "side": order.side,
                        "qty": q_req,
                        "price": request.price,
                        "commission": commission,
                    },
                    outputs={"order_id": order.id, "reason": why},
                    ts=now,
                    message=f"guardrail breach: {why}",
                )
            )
            raise GuardrailBreach(why)

        # Apply the fill
        if order.side == "BUY":
            pos.qty += q_req
            pos.cash -= (q_req * request.price) + commission
        else:
            # SELL
            pos.qty -= q_req
            pos.cash += (q_req * request.price) - commission

        # Create and persist trade record
        from domain.entities.trade import Trade

        trade = Trade(
            id=f"trd_{uuid4().hex[:8]}",
            order_id=order.id,
            position_id=order.position_id,
            side=order.side,  # OrderSide is a Literal type, so we can use the string directly
            qty=q_req,
            price=request.price,
            commission=commission,
            executed_at=now,
        )
        self.trades.save(trade)

        self.positions.save(pos)

        order.status = "filled"
        self.orders.save(order)

        # Update anchor price after successful execution
        pos.set_anchor_price(request.price)

        self.events.append(
            Event(
                id=f"evt_filled_{order.id}_{uid}",
                position_id=order.position_id,
                type="order_filled",
                inputs={"qty": q_req, "price": request.price},
                outputs={"order_id": order.id},
                ts=now,
                message=f"order filled ({order.side} {q_req})",
            )
        )

        # Log anchor price update
        self.events.append(
            Event(
                id=f"evt_anchor_{order.id}_{uid}",
                position_id=order.position_id,
                type="anchor_updated",
                inputs={"old_anchor": pos.anchor_price, "new_anchor": request.price},
                outputs={"anchor_price": request.price},
                ts=now,
                message=f"Anchor price updated to ${request.price:.2f}",
            )
        )

        return FillOrderResponse(order_id=order.id, status="filled", filled_qty=q_req)

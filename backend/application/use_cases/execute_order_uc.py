# =========================
# backend/application/use_cases/execute_order_uc.py
# =========================
from application.dto.orders import FillOrderRequest, FillOrderResponse
from domain.entities.event import Event
from domain.errors import GuardrailBreach


class ExecuteOrderUC:
    """Flow C: Apply fills to update position balances and emit an event."""

    def __init__(self, positions, orders, events, clock) -> None:
        self.positions = positions
        self.orders = orders
        self.events = events
        self.clock = clock

    def execute(self, order_id: str, request: FillOrderRequest) -> FillOrderResponse:
        order = self.orders.get(order_id)
        if not order:
            raise KeyError("order_not_found")
        pos = self.positions.get(order.position_id)
        if not pos:
            raise KeyError("position_not_found")

        # Guardrails: no negative cash on BUY
        gross = request.filled_qty * request.price
        if order.side == "BUY":
            total_cost = gross + request.commission
            if pos.cash + 1e-9 < total_cost:  # small epsilon for float jitter
                raise GuardrailBreach("insufficient_cash_for_buy")
        else:  # SELL
            if pos.qty + 1e-9 < request.filled_qty:
                raise GuardrailBreach("insufficient_qty_for_sell")

        # Cash/qty math
        if order.side == "BUY":
            pos.qty += request.filled_qty
            pos.cash -= gross + request.commission
        else:
            pos.qty -= request.filled_qty
            pos.cash += gross - request.commission

        # Persist position and order
        self.positions.save(pos)
        order.status = "filled"
        self.orders.save(order)

        # Emit event
        evt = Event(
            id=f"evt_fill_{order.id}",
            position_id=order.position_id,
            type="order_filled",
            inputs={
                "order_id": order.id,
                "side": order.side,
                "filled_qty": request.filled_qty,
                "price": request.price,
                "commission": request.commission,
            },
            outputs={
                "position_qty": pos.qty,
                "position_cash": pos.cash,
            },
            message=f"order filled ({order.side} {request.filled_qty} @ {request.price})",
            ts=self.clock.now(),
        )
        self.events.append(evt)

        return FillOrderResponse(
            order_id=order_id,
            status=order.status,
            position_qty=pos.qty,
            position_cash=pos.cash,
        )

# =========================
# backend/application/use_cases/execute_order_uc.py
# =========================
from application.dto.orders import FillOrderRequest, FillOrderResponse

class ExecuteOrderUC:
    """Flow C: Apply fills to update position balances (placeholder)."""

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
        # TODO: implement proper cash/qty math and guardrail checks
        if order.side == "BUY":
            pos.qty += request.filled_qty
            pos.cash -= request.filled_qty * request.price + request.commission
        else:
            pos.qty -= request.filled_qty
            pos.cash += request.filled_qty * request.price - request.commission
        self.positions.save(pos)
        order.status = "filled"
        self.orders.save(order)
        return FillOrderResponse(
            order_id=order_id,
            status=order.status,
            position_qty=pos.qty,
            position_cash=pos.cash,
        )

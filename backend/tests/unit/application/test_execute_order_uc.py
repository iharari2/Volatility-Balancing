import pytest
from app.di import container
from application.use_cases.execute_order_uc import ExecuteOrderUC
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.dto.orders import CreateOrderRequest, FillOrderRequest
from domain.errors import GuardrailBreach


def _submit_buy_order(pos_id: str, qty: float = 2.0):
    uc = SubmitOrderUC(
        container.positions,
        container.orders,
        container.idempotency,
        container.events,
        container.clock,
    )
    resp, _ = uc.execute(
        position_id=pos_id,
        request=CreateOrderRequest(side="BUY", qty=qty),
        idempotency_key="K-fill",
    )
    return resp.order_id


def test_fill_buy_increases_qty_and_decreases_cash():
    pos = container.positions.create(ticker="AAA", qty=0.0, cash=1000.0)
    oid = _submit_buy_order(pos.id, qty=2.0)
    uc = ExecuteOrderUC(container.positions, container.orders, container.events, container.clock)
    r = uc.execute(
        order_id=oid, request=FillOrderRequest(price=10.0, filled_qty=2.0, commission=1.0)
    )
    assert r.status == "filled"
    assert r.position_qty == 2.0
    assert r.position_cash == pytest.approx(1000.0 - (2 * 10.0) - 1.0)


def test_fill_sell_rejects_if_insufficient_qty():
    pos = container.positions.create(ticker="BBB", qty=1.0, cash=0.0)
    # craft a SELL order directly
    from domain.entities.order import Order

    container.orders.save(Order(id="ord_sell", position_id=pos.id, side="SELL", qty=1.0))
    uc = ExecuteOrderUC(container.positions, container.orders, container.events, container.clock)
    with pytest.raises(GuardrailBreach):
        uc.execute(
            order_id="ord_sell", request=FillOrderRequest(price=5.0, filled_qty=2.0, commission=0.0)
        )

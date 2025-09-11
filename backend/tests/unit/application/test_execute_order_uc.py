import pytest
from app.di import container
from application.use_cases.execute_order_uc import ExecuteOrderUC
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.dto.orders import CreateOrderRequest, FillOrderRequest
from domain.errors import GuardrailBreach


def _submit_buy_order(pos_id: str, qty: float = 2.0):
    from application.use_cases.submit_order_uc import SubmitOrderUC
    from application.dto.orders import CreateOrderRequest

    uc = SubmitOrderUC(
        container.positions,
        container.orders,
        container.idempotency,
        container.events,
        container.clock,
    )
    resp = uc.execute(  # was: resp, _ = uc.execute(...)
        position_id=pos_id,
        request=CreateOrderRequest(side="BUY", qty=qty),
        idempotency_key="K-fill",
    )
    return resp.order_id


def test_fill_buy_increases_qty_and_decreases_cash():
    pos = container.positions.create(ticker="AAA", qty=0.0, cash=1000.0)
    oid = _submit_buy_order(pos.id, qty=2.0)
    uc = ExecuteOrderUC(container.positions, container.orders, container.events, container.clock)
    r = uc.execute(order_id=oid, request=FillOrderRequest(qty=2.0, price=10.0, commission=1.0))
    pos_after = container.positions.get(pos.id)
    assert pos_after.qty == 2.0
    assert pos_after.cash == 1000.0 - (2.0 * 10.0) - 1.0  # price*qty + commission
    assert r.filled_qty == 2.0
    assert r.status == "filled"


def test_fill_sell_rejects_if_insufficient_qty():
    pos = container.positions.create(ticker="BBB", qty=1.0, cash=0.0)
    # craft a SELL order directly
    from domain.entities.order import Order

    container.orders.save(
        Order(
            id="ord_sell", position_id=pos.id, side="SELL", qty=1.0, idempotency_key="test-sell-1"
        )
    )

    uc = ExecuteOrderUC(container.positions, container.orders, container.events, container.clock)
    with pytest.raises(GuardrailBreach):
        uc.execute(order_id="ord_sell", request=FillOrderRequest(qty=2.0, price=5.0))


def test_buy_commission_decreases_cash(container):
    pos = container.positions.create(ticker="AAA", qty=0.0, cash=1000.0)
    oid = container.orders.create(position_id=pos.id, side="BUY", qty=2.0, idempotency_key="buy-1")

    uc = ExecuteOrderUC(container.positions, container.orders, container.events, container.clock)
    uc.execute(order_id=oid, request=FillOrderRequest(qty=2.0, price=10.0, commission=1.0))

    pos_after = container.positions.get(pos.id)
    assert pos_after.qty == 2.0
    # 1000 - (2 * 10) - 1
    assert pos_after.cash == 979.0


def test_sell_commission_reduces_proceeds(container):
    pos = container.positions.create(ticker="BBB", qty=5.0, cash=0.0)
    oid = container.orders.create(
        position_id=pos.id, side="SELL", qty=2.0, idempotency_key="sell-1"
    )

    uc = ExecuteOrderUC(container.positions, container.orders, container.events, container.clock)
    uc.execute(order_id=oid, request=FillOrderRequest(qty=2.0, price=10.0, commission=1.5))

    pos_after = container.positions.get(pos.id)
    assert pos_after.qty == 3.0
    # + (2 * 10) - 1.5
    assert pos_after.cash == 18.5


def test_commission_defaults_to_zero(container):
    pos = container.positions.create(ticker="CCC", qty=0.0, cash=100.0)
    oid = container.orders.create(position_id=pos.id, side="BUY", qty=1.0, idempotency_key="buy-2")
    uc = ExecuteOrderUC(container.positions, container.orders, container.events, container.clock)
    uc.execute(order_id=oid, request=FillOrderRequest(qty=1.0, price=10.0))  # no commission
    pos_after = container.positions.get(pos.id)
    assert pos_after.qty == 1.0
    assert pos_after.cash == 90.0  # 100 - 10

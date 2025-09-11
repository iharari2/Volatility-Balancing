from application.use_cases.execute_order_uc import ExecuteOrderUC
from application.dto.orders import FillOrderRequest
from domain.value_objects.order_policy import OrderPolicy
from domain.entities.position import Position
from domain.entities.order import Order


def make_pos(policy: OrderPolicy) -> Position:
    from datetime import datetime, timezone

    return Position(
        id="pos1",
        ticker="ZIM",
        qty=0,
        cash=1000.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        order_policy=policy,
    )


def test_fill_below_min_qty_hold(mocker):
    policy = OrderPolicy(min_qty=5.0, action_below_min="hold")
    pos = make_pos(policy)
    orders = mocker.Mock()
    positions = mocker.Mock()
    positions.get.return_value = pos

    events = mocker.Mock()
    clock = mocker.Mock()
    uc = ExecuteOrderUC(positions=positions, orders=orders, events=events, clock=clock)

    # Pretend order exists
    order = Order(id="o1", position_id="pos1", side="BUY", qty=1.0, status="submitted")
    orders.get.return_value = order

    resp = uc.execute(order_id="o1", request=FillOrderRequest(qty=1.0, price=10.0, commission=0.0))
    assert resp.filled_qty == 0.0
    assert resp.status == "skipped"
    events.append.assert_called()  # skipped event


def test_fill_below_min_qty_reject(mocker):
    policy = OrderPolicy(min_qty=5.0, action_below_min="reject")
    pos = make_pos(policy)
    positions = mocker.Mock(get=lambda *_: pos)
    orders = mocker.Mock(
        get=lambda *_: Order(id="o1", position_id="pos1", side="BUY", qty=1.0, status="submitted")
    )
    events = mocker.Mock()
    clock = mocker.Mock()
    uc = ExecuteOrderUC(positions=positions, orders=orders, events=events, clock=clock)

    resp = uc.execute(order_id="o1", request=FillOrderRequest(qty=1.0, price=10.0))
    assert resp.status == "rejected"
    events.append.assert_called()

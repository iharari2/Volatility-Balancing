import pytest
from app.di import container
from application.use_cases.execute_order_uc import ExecuteOrderUC
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.dto.orders import CreateOrderRequest, FillOrderRequest
from domain.errors import GuardrailBreach
from domain.entities.portfolio import Portfolio
from domain.entities.order import Order


def _setup_test_portfolio(
    tenant_id: str = "default", portfolio_id: str = "test_portfolio", cash_balance: float = 1000.0
):
    """Helper to create a test portfolio. Cash is now stored in Position entity."""
    portfolio = Portfolio(id=portfolio_id, tenant_id=tenant_id, name="Test")
    container.portfolio_repo.save(portfolio)
    # Note: Cash is now stored in Position.cash, not PortfolioCash
    return tenant_id, portfolio_id


def _submit_buy_order(tenant_id: str, portfolio_id: str, pos_id: str, qty: float = 2.0):
    uc = SubmitOrderUC(
        container.positions,
        container.orders,
        container.idempotency,
        container.events,
        container.config,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
    )
    resp = uc.execute(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=pos_id,
        request=CreateOrderRequest(side="BUY", qty=qty),
        idempotency_key="K-fill",
    )
    return resp.order_id


def test_fill_buy_increases_qty_and_decreases_cash():
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=1000.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="AAA", qty=0.0
    )
    # Set initial cash on position (cash lives in Position entity)
    pos.cash = 1000.0
    container.positions.save(pos)
    oid = _submit_buy_order(tenant_id, portfolio_id, pos.id, qty=2.0)
    uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    r = uc.execute(order_id=oid, request=FillOrderRequest(qty=2.0, price=50.0, commission=1.0))
    pos_after = container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=pos.id
    )
    assert pos_after.qty == 2.0
    assert pos_after.cash == 1000.0 - (2.0 * 50.0) - 1.0
    assert r.filled_qty == 2.0
    assert r.status == "filled"


def test_fill_sell_rejects_if_insufficient_qty():
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=0.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="BBB", qty=1.0
    )
    container.orders.save(
        Order(
            id="ord_sell",
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=pos.id,
            side="SELL",
            qty=1.0,
            idempotency_key="test-sell-1",
        )
    )
    uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    with pytest.raises(GuardrailBreach):
        uc.execute(order_id="ord_sell", request=FillOrderRequest(qty=2.0, price=50.0))


def test_buy_commission_decreases_cash():
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=1000.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="AAA", qty=0.0
    )
    # Set initial cash on position (cash lives in Position entity)
    pos.cash = 1000.0
    container.positions.save(pos)
    oid = container.orders.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=pos.id,
        side="BUY",
        qty=2.0,
        idempotency_key="buy-1",
    )
    uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    uc.execute(order_id=oid, request=FillOrderRequest(qty=2.0, price=50.0, commission=1.0))
    pos_after = container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=pos.id
    )
    assert pos_after.qty == 2.0
    assert pos_after.cash == 899.0


def test_sell_commission_reduces_proceeds():
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=0.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="BBB", qty=5.0
    )
    # Set initial cash on position (cash lives in Position entity)
    pos.cash = 0.0
    container.positions.save(pos)
    oid = container.orders.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=pos.id,
        side="SELL",
        qty=2.0,
        idempotency_key="sell-1",
    )
    uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    uc.execute(order_id=oid, request=FillOrderRequest(qty=2.0, price=50.0, commission=1.5))
    pos_after = container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=pos.id
    )
    assert pos_after.qty == 3.0
    assert pos_after.cash == 98.5


def test_commission_defaults_to_zero():
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=100.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="CCC", qty=0.0
    )
    # Set initial cash on position (cash lives in Position entity)
    pos.cash = 100.0
    container.positions.save(pos)
    oid = container.orders.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=pos.id,
        side="BUY",
        qty=1.0,
        idempotency_key="buy-2",
    )
    uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    uc.execute(order_id=oid, request=FillOrderRequest(qty=1.0, price=100.0))
    pos_after = container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=pos.id
    )
    assert pos_after.qty == 1.0
    assert pos_after.cash == 0.0


def test_commission_aggregate_increment_on_buy():
    """Test that total_commission_paid is incremented on buy order execution."""
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=1000.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="DDD", qty=0.0
    )
    # Set initial cash on position (cash lives in Position entity)
    pos.cash = 1000.0
    container.positions.save(pos)
    oid = container.orders.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=pos.id,
        side="BUY",
        qty=2.0,
        idempotency_key="buy-3",
    )
    uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    assert pos.total_commission_paid == 0.0
    uc.execute(order_id=oid, request=FillOrderRequest(qty=2.0, price=50.0, commission=1.0))
    pos_after = container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=pos.id
    )
    assert pos_after.total_commission_paid == 1.0


def test_commission_aggregate_increment_on_sell():
    """Test that total_commission_paid is incremented on sell order execution."""
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=0.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="EEE", qty=5.0
    )
    # Set initial cash on position (cash lives in Position entity)
    pos.cash = 0.0
    container.positions.save(pos)
    oid = container.orders.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=pos.id,
        side="SELL",
        qty=2.0,
        idempotency_key="sell-2",
    )
    uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    assert pos.total_commission_paid == 0.0
    uc.execute(order_id=oid, request=FillOrderRequest(qty=2.0, price=50.0, commission=1.5))
    pos_after = container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=pos.id
    )
    assert pos_after.total_commission_paid == 1.5


def test_commission_aggregate_multiple_trades():
    """Test that total_commission_paid aggregates across multiple trades."""
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=2000.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="FFF", qty=0.0
    )
    # Set initial cash on position (cash lives in Position entity)
    pos.cash = 2000.0
    container.positions.save(pos)
    uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    commissions = [1.0, 1.5, 2.0]
    for i, commission in enumerate(commissions):
        oid = container.orders.create(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=pos.id,
            side="BUY",
            qty=2.0,
            idempotency_key=f"buy-{i}",
        )
        uc.execute(
            order_id=oid, request=FillOrderRequest(qty=2.0, price=50.0, commission=commission)
        )
        pos = container.positions.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=pos.id
        )
    pos_after = container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=pos.id
    )
    expected_total = sum(commissions)
    assert pos_after.total_commission_paid == expected_total
    assert pos_after.total_commission_paid == 4.5


def test_trade_commission_rate_effective_set():
    """Test that commission_rate_effective is set in trade."""
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=1000.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="GGG", qty=0.0
    )
    # Set initial cash on position (cash lives in Position entity)
    pos.cash = 1000.0
    container.positions.save(pos)
    oid = container.orders.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=pos.id,
        side="BUY",
        qty=2.0,
        idempotency_key="buy-4",
    )
    uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    uc.execute(order_id=oid, request=FillOrderRequest(qty=2.0, price=50.0, commission=1.0))
    trades = list(container.trades.list_for_order(oid))
    assert len(trades) == 1
    trade = trades[0]
    assert trade.commission_rate_effective == 0.01
    assert trade.commission == 1.0


def test_trade_status_defaults_to_executed():
    """Test that trade status defaults to 'executed'."""
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=1000.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="HHH", qty=0.0
    )
    # Set initial cash on position (cash lives in Position entity)
    pos.cash = 1000.0
    container.positions.save(pos)
    oid = container.orders.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=pos.id,
        side="BUY",
        qty=2.0,
        idempotency_key="buy-5",
    )
    uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    uc.execute(order_id=oid, request=FillOrderRequest(qty=2.0, price=50.0, commission=1.0))
    trades = list(container.trades.list_for_order(oid))
    assert len(trades) == 1
    trade = trades[0]
    assert trade.status == "executed"


def test_commission_aggregate_starts_at_zero():
    """Test that new positions start with total_commission_paid = 0.0."""
    tenant_id, portfolio_id = _setup_test_portfolio(cash_balance=1000.0)
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="III", qty=0.0
    )
    assert pos.total_commission_paid == 0.0

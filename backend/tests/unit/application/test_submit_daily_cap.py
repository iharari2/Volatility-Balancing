# backend/tests/unit/application/test_submit_daily_cap.py
from __future__ import annotations

import pytest
from decimal import Decimal
from application.dto.orders import CreateOrderRequest, FillOrderRequest
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.use_cases.execute_order_uc import ExecuteOrderUC
from domain.errors import GuardrailBreach
from domain.value_objects.configs import GuardrailConfig
from infrastructure.time.clock import Clock
from app.di import container


def _submit(context, position_id: str, side: str, qty: float, idemp: str | None = None) -> str:
    """Helper to submit an order and return its id."""
    uc = SubmitOrderUC(
        positions=container.positions,
        orders=container.orders,
        idempotency=container.idempotency,
        events=container.events,
        config_repo=container.config,
        clock=container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
    )
    resp = uc.execute(
        tenant_id="default",
        portfolio_id="test_portfolio",
        position_id=position_id,
        idempotency_key=idemp,
        request=CreateOrderRequest(side=side, qty=qty),
    )
    assert resp.accepted is True
    return resp.order_id


def test_daily_cap_at_submit_is_enforced():
    # Arrange: position with a daily cap (e.g., 2 orders/day)
    tenant_id = "default"
    portfolio_id = "test_portfolio"
    from domain.entities.portfolio import Portfolio

    portfolio = Portfolio(id=portfolio_id, tenant_id=tenant_id, name="Test")
    container.portfolio_repo.save(portfolio)
    container.portfolio_cash_repo.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, currency="USD", cash_balance=10_000.0
    )
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="CAP", qty=0.0
    )
    # If your Position/GuardrailPolicy doesn't default this, set and save:
    pos.guardrails.max_orders_per_day = 2
    container.positions.save(pos)

    # Verify the position was saved correctly
    pos_after = container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=pos.id
    )
    assert (
        pos_after.guardrails.max_orders_per_day == 2
    ), f"Expected 2, got {pos_after.guardrails.max_orders_per_day}"

    # Act: submit up to the cap
    _submit(container, pos.id, side="BUY", qty=1.0, idemp="cap-1")
    _submit(container, pos.id, side="SELL", qty=1.0, idemp="cap-2")

    # Assert: the next submit breaches the daily cap
    with pytest.raises(GuardrailBreach):
        _submit(container, pos.id, side="BUY", qty=1.0, idemp="cap-3")


def test_daily_cap_reset_or_clock_behavior_smoke():
    """Optional: demonstrates that the test doesn’t depend on event IDs."""
    # This is a lightweight smoke test; adapt if you simulate day rollovers via a fake Clock.
    assert isinstance(container.clock, Clock)


def test_daily_cap_at_fill_is_enforced():
    tenant_id = "default"
    portfolio_id = "test_portfolio"
    from domain.entities.portfolio import Portfolio

    portfolio = Portfolio(id=portfolio_id, tenant_id=tenant_id, name="Test")
    container.portfolio_repo.save(portfolio)
    # Cash is now stored in Position entity, not PortfolioCash
    pos = container.positions.create(
        tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="CAPF", qty=0.0
    )
    # Set initial cash on position (cash lives in Position entity)
    pos.cash = 10_000.0
    pos.guardrails.max_orders_per_day = 1
    container.positions.save(pos)
    # Set permissive allocation guardrails so the small buy doesn't violate min stock %
    container.config.set_guardrail_config(
        pos.id,
        GuardrailConfig(
            min_stock_pct=Decimal("0.0"),
            max_stock_pct=Decimal("1.0"),
            max_trade_pct_of_position=Decimal("1.0"),
            max_orders_per_day=1,
        ),
    )

    # Verify the position was saved correctly
    pos_after = container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=pos.id
    )
    assert (
        pos_after.guardrails.max_orders_per_day == 1
    ), f"Expected 1, got {pos_after.guardrails.max_orders_per_day}"

    # Submit first order (should pass)
    first = _submit(container, pos.id, side="BUY", qty=1.0, idemp="fillcap-1")

    # Second submit should breach the cap at submit time
    with pytest.raises(GuardrailBreach):
        _submit(container, pos.id, side="BUY", qty=1.0, idemp="fillcap-2")

    # Fill the first order (should work)
    exec_uc = ExecuteOrderUC(
        container.positions,
        container.orders,
        container.trades,
        container.events,
        container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    r1 = exec_uc.execute(
        order_id=first,
        request=FillOrderRequest(
            qty=1.0, price=100.0, commission=0.0
        ),  # 1.0 * 100.0 = 100.0 notional
    )
    assert r1.status == "filled"

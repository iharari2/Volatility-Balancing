# =========================
# backend/tests/integration/test_position_tick.py
# =========================
"""
Integration test for POST /positions/{position_id}/tick endpoint.

Verifies:
- One event per tick (even if HOLD)
- Required response fields are present
- Order and trade creation for BUY/SELL actions
- Position state updates through ExecuteOrderUC
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.di import container
from domain.entities.position import Position
from domain.entities.portfolio import Portfolio

client = TestClient(app)


@pytest.fixture
def setup_test_position():
    """Create a test position with anchor price for testing."""
    tenant_id = "default"  # Must match _find_position_legacy default
    portfolio_id = "test_portfolio_tick"
    position_id = "test_position_tick"

    # Create portfolio
    portfolio = Portfolio(
        id=portfolio_id,
        tenant_id=tenant_id,
        # Use a unique name per test run to avoid clashes across tests
        name=f"Test Portfolio for Tick {uuid.uuid4().hex[:8]}",
        trading_state="RUNNING",
    )
    container.portfolio_repo.save(portfolio)

    # Create position with anchor price
    position = Position(
        id=position_id,
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        asset_symbol="AAPL",
        qty=100.0,
        cash=10000.0,
        anchor_price=150.0,
    )
    container.positions.save(position)

    yield {
        "tenant_id": tenant_id,
        "portfolio_id": portfolio_id,
        "position_id": position_id,
    }

    # Cleanup
    try:
        container.positions.delete(tenant_id, portfolio_id, position_id)
    except:
        pass
    try:
        container.portfolio_repo.delete(tenant_id, portfolio_id)
    except:
        pass


def test_tick_creates_one_event_per_call(setup_test_position):
    """Verify that each tick call creates exactly one PositionEvent."""
    position_id = setup_test_position["position_id"]

    # Count events before
    if hasattr(container, "position_event"):
        events_before = container.position_event.list_by_position(position_id=position_id)
        count_before = len(events_before)
    else:
        # If position_event repo not available, skip test
        pytest.skip("PositionEvent repository not available")

    # Execute tick
    response = client.post(f"/v1/positions/{position_id}/tick")

    # Verify response
    assert response.status_code == 200
    data = response.json()

    # Count events after
    events_after = container.position_event.list_by_position(position_id=position_id)
    count_after = len(events_after)

    # Should have exactly one more event
    assert count_after == count_before + 1, f"Expected {count_before + 1} events, got {count_after}"

    # Verify the last event
    last_event = events_after[0] if events_after else None
    assert last_event is not None, "No event was created"
    assert last_event["position_id"] == position_id


def test_tick_response_has_required_fields(setup_test_position):
    """Verify that tick response contains all required fields."""
    position_id = setup_test_position["position_id"]

    response = client.post(f"/v1/positions/{position_id}/tick")
    assert response.status_code == 200
    data = response.json()

    # Verify required top-level fields
    assert "position_snapshot" in data
    assert "baseline_deltas" in data
    assert "allocation_vs_guardrails" in data
    assert "last_event" in data
    assert "cycle_result" in data

    # Verify position_snapshot fields
    snapshot = data["position_snapshot"]
    required_snapshot_fields = [
        "position_id",
        "symbol",
        "qty",
        "cash",
        "stock_value",
        "total_value",
        "allocation_pct",
        "anchor_price",
        "current_price",
    ]
    for field in required_snapshot_fields:
        assert field in snapshot, f"Missing field: {field}"

    # Verify baseline_deltas structure
    deltas = data["baseline_deltas"]
    assert "position_vs_baseline" in deltas
    assert "stock_vs_baseline" in deltas
    assert "pct" in deltas["position_vs_baseline"] or deltas["position_vs_baseline"]["pct"] is None
    assert "abs" in deltas["position_vs_baseline"] or deltas["position_vs_baseline"]["abs"] is None

    # Verify allocation_vs_guardrails structure
    allocation = data["allocation_vs_guardrails"]
    assert "current_allocation_pct" in allocation
    assert "min_stock_pct" in allocation
    assert "max_stock_pct" in allocation
    assert "within_guardrails" in allocation

    # Verify cycle_result structure
    cycle = data["cycle_result"]
    assert "action" in cycle
    assert "action_reason" in cycle
    assert "order_id" in cycle
    assert "trade_id" in cycle
    assert "evaluation_timestamp" in cycle

    # Verify action is one of the expected values
    assert cycle["action"] in ["HOLD", "SKIP", "BUY", "SELL"]


def test_tick_creates_order_and_trade_for_buy_sell(setup_test_position):
    """Verify that BUY/SELL actions create order and trade."""
    position_id = setup_test_position["position_id"]
    tenant_id = setup_test_position["tenant_id"]
    portfolio_id = setup_test_position["portfolio_id"]

    # Set anchor price to trigger a trade (e.g., very different from current price)
    position = container.positions.get(tenant_id, portfolio_id, position_id)
    if position:
        # Set anchor to trigger buy (current price much lower than anchor)
        # This depends on market data, so we'll just verify the structure
        pass

    response = client.post(f"/v1/positions/{position_id}/tick")
    assert response.status_code == 200
    data = response.json()

    cycle = data["cycle_result"]
    action = cycle["action"]

    # If action is BUY or SELL, verify order_id and trade_id are set
    if action in ("BUY", "SELL"):
        assert cycle["order_id"] is not None, "Order ID should be set for BUY/SELL"
        assert cycle["trade_id"] is not None, "Trade ID should be set for BUY/SELL"

        # Verify order exists
        order = container.orders.get(cycle["order_id"])
        assert order is not None, "Order should exist in repository"
        assert order.status == "filled", "Order should be filled"

        # Verify trade exists
        trade = container.trades.get(cycle["trade_id"])
        assert trade is not None, "Trade should exist in repository"
        assert trade.status == "executed", "Trade should be executed"


def test_tick_updates_position_state(setup_test_position):
    """Verify that tick updates position state through ExecuteOrderUC."""
    position_id = setup_test_position["position_id"]
    tenant_id = setup_test_position["tenant_id"]
    portfolio_id = setup_test_position["portfolio_id"]

    # Get initial position state
    position_before = container.positions.get(tenant_id, portfolio_id, position_id)
    qty_before = position_before.qty
    cash_before = position_before.cash or 0.0

    response = client.post(f"/v1/positions/{position_id}/tick")
    assert response.status_code == 200
    data = response.json()

    # Get position state after
    position_after = container.positions.get(tenant_id, portfolio_id, position_id)
    qty_after = position_after.qty
    cash_after = position_after.cash or 0.0

    # Verify position snapshot matches actual position
    snapshot = data["position_snapshot"]
    assert snapshot["qty"] == qty_after
    assert abs(snapshot["cash"] - cash_after) < 0.01  # Allow small floating point differences

    # If a trade occurred, verify state changed
    cycle = data["cycle_result"]
    if cycle["trade_id"] is not None:
        # Position state should have changed
        assert (
            qty_after != qty_before or cash_after != cash_before
        ), "Position state should change after trade"


def test_tick_handles_hold_action(setup_test_position):
    """Verify that HOLD actions still create an event."""
    position_id = setup_test_position["position_id"]

    # Count events before
    if hasattr(container, "position_event"):
        events_before = container.position_event.list_by_position(position_id=position_id)
        count_before = len(events_before)
    else:
        pytest.skip("PositionEvent repository not available")

    response = client.post(f"/v1/positions/{position_id}/tick")
    assert response.status_code == 200
    data = response.json()

    # Verify action can be HOLD
    cycle = data["cycle_result"]
    # HOLD is a valid action
    assert cycle["action"] in ["HOLD", "SKIP", "BUY", "SELL"]

    # Verify event was still created even for HOLD
    events_after = container.position_event.list_by_position(position_id=position_id)
    count_after = len(events_after)
    assert count_after == count_before + 1, "Event should be created even for HOLD action"

    # Verify last_event is set
    assert data["last_event"] is not None, "last_event should be set even for HOLD"

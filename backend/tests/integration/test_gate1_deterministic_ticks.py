from __future__ import annotations

import uuid
import os
import time

import pytest

from app.di import container
from domain.entities.position import Position
from domain.entities.portfolio import Portfolio
from infrastructure.market.deterministic_market_data import DeterministicMarketDataAdapter


@pytest.fixture
def deterministic_position():
    deterministic = DeterministicMarketDataAdapter()
    container.market_data = deterministic
    container.evaluate_position_uc.market_data = deterministic

    tenant_id = "default"
    portfolio_id = f"gate1_portfolio_{uuid.uuid4().hex[:8]}"
    position_id = f"gate1_position_{uuid.uuid4().hex[:8]}"

    portfolio = Portfolio(
        id=portfolio_id,
        tenant_id=tenant_id,
        name=f"Gate1 Portfolio {uuid.uuid4().hex[:6]}",
        trading_state="RUNNING",
        trading_hours_policy="OPEN_PLUS_AFTER_HOURS",
    )
    container.portfolio_repo.save(portfolio)

    anchor_price = deterministic.get_price("AAPL").price
    position = Position(
        id=position_id,
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        asset_symbol="AAPL",
        qty=10.0,
        cash=10000.0,
        anchor_price=anchor_price,
    )
    position.guardrails.max_orders_per_day = 50
    container.positions.save(position)

    return {
        "tenant_id": tenant_id,
        "portfolio_id": portfolio_id,
        "position_id": position_id,
    }


@pytest.mark.anyio
async def test_deterministic_ticks_produce_buy_and_sell(async_client, deterministic_position):
    position_id = deterministic_position["position_id"]

    actions = []
    debug_gate1 = os.getenv("VB_DEBUG_GATE1") == "1"
    for tick_index in range(10):
        if os.getenv("VB_TIMING"):
            start = time.perf_counter()
            print(f"[tick] request start position_id={position_id}")
        response = await async_client.post(f"/v1/positions/{position_id}/tick")
        if os.getenv("VB_TIMING"):
            elapsed = time.perf_counter() - start
            print(f"[tick] request done position_id={position_id} elapsed={elapsed:.4f}s")
        assert response.status_code == 200
        payload = response.json()
        cycle_result = payload.get("cycle_result", {})
        action = cycle_result.get("action")
        actions.append(action)
        if debug_gate1:
            print(
                "[gate1-debug] tick_index="
                f"{tick_index} action={action} "
                f"trigger_direction={cycle_result.get('trigger_direction')} "
                f"action_reason={cycle_result.get('action_reason')}"
            )

    assert "BUY" in actions, f"Expected at least one BUY, got {actions}"
    assert "SELL" in actions, f"Expected at least one SELL, got {actions}"


@pytest.mark.anyio
async def test_deterministic_timeline_increases_by_ten(async_client, deterministic_position):
    tenant_id = deterministic_position["tenant_id"]
    portfolio_id = deterministic_position["portfolio_id"]
    position_id = deterministic_position["position_id"]

    before = container.evaluation_timeline.list_by_position(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=position_id,
        mode="LIVE",
        limit=200,
    )

    for _ in range(10):
        if os.getenv("VB_TIMING"):
            start = time.perf_counter()
            print(f"[tick] request start position_id={position_id}")
        response = await async_client.post(f"/v1/positions/{position_id}/tick")
        if os.getenv("VB_TIMING"):
            elapsed = time.perf_counter() - start
            print(f"[tick] request done position_id={position_id} elapsed={elapsed:.4f}s")
        assert response.status_code == 200

    after = container.evaluation_timeline.list_by_position(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=position_id,
        mode="LIVE",
        limit=200,
    )
    # Each tick writes an evaluation record; ticks that execute a trade also
    # write an EXECUTION record, so the total is ≥ 10.
    assert len(after) >= len(before) + 10

    response = await async_client.get(f"/v1/positions/{position_id}/timeline?limit=200")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == len(after)

    sample = rows[0]
    for field in [
        "timestamp",
        "action",
        "trigger_direction",
        "current_price",
        "guardrail_min_stock_pct",
        "guardrail_max_stock_pct",
        "allocation_after",
    ]:
        assert field in sample, f"Missing field {field} in timeline response"


@pytest.mark.anyio
async def test_async_healthz_over_async_client(async_client):
    response = await async_client.get("/v1/healthz")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("healthy", "degraded", "unhealthy")

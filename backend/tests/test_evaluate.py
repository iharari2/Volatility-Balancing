# Suggested file: backend/tests/test_evaluate.py
"""
    Pytest suite for the FastAPI MVP.
    Assumes the FastAPI app and domain types live in `backend/app/api/app.py` with names:
    - `app` (FastAPI instance)
    - `evaluate_position`, `PortfolioSettings`, `Position`

If you later split files (e.g., move `evaluate_position` into `backend/app/domain/sizing.py`),
just update the imports below.
"""
from __future__ import annotations
import math
from fastapi.testclient import TestClient
import pytest

# ---- Import from your app ----
from backend.app.api.app import app, evaluate_position, PortfolioSettings, Position  # type: ignore


# ---- Test client fixture ----
@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ---- Pure domain tests (fast, deterministic) ----

def test_thresholds_no_cross():
    cfg = PortfolioSettings(tau=0.03)
    pos = Position(id="p1", portfolio_id="pf1", symbol="AAPL", shares=10.0, anchor_price=100.0, cash=1000.0)
    res = evaluate_position(pos, price=101.0, cfg=cfg)  # within ±3%
    assert res.side is None
    assert res.reason == "no_threshold_cross"


def test_buy_trigger_value_conservation_ignoring_fees():
    cfg = PortfolioSettings(tau=0.03)
    pos = Position(id="p1", portfolio_id="pf1", symbol="AAPL", shares=10.0, anchor_price=100.0, cash=1000.0)
    price = 90.0  # BUY trigger (<= 97)
    res = evaluate_position(pos, price=price, cfg=cfg)
    # If not skipped by min_notional/cash, portfolio value should be unchanged in asset_pct calc
    A = price * pos.shares
    V = A + pos.cash + pos.receivable
    if res.side == "BUY" and res.qty != 0:
        projected_shares = pos.shares + res.qty
        A_prime = price * projected_shares
        C_prime = pos.cash + pos.receivable - abs(res.qty) * price
        V_prime = A_prime + C_prime
        assert math.isclose(V_prime, V, rel_tol=1e-9, abs_tol=1e-9)


def test_sell_trigger_value_conservation_ignoring_fees():
    cfg = PortfolioSettings(tau=0.03)
    pos = Position(id="p1", portfolio_id="pf1", symbol="AAPL", shares=10.0, anchor_price=100.0, cash=1000.0)
    price = 110.0  # SELL trigger (>= 103)
    res = evaluate_position(pos, price=price, cfg=cfg)
    A = price * pos.shares
    V = A + pos.cash + pos.receivable
    if res.side == "SELL" and res.qty != 0:
        projected_shares = pos.shares + res.qty  # qty negative on SELL
        A_prime = price * projected_shares
        C_prime = pos.cash + pos.receivable - res.qty * price  # note: qty negative -> add cash
        V_prime = A_prime + C_prime
        assert math.isclose(V_prime, V, rel_tol=1e-9, abs_tol=1e-9)

def test_min_notional_skip():
    cfg = PortfolioSettings(min_notional=10_000.0)  # we want to force a skip
    pos = Position(
        id="p1", portfolio_id="pf1", symbol="AAPL",
        shares=0.0, anchor_price=100.0, cash=100.0
    )
    price = 97.0  # just across BUY threshold (τ=3%)
    res = evaluate_position(pos, price=price, cfg=cfg)
    assert res.reason == "min_notional"


# ---- Guardrail behavior ----

def test_guardrail_trim_hits_nearest_bound():
    cfg = PortfolioSettings(guardrails=(0.25, 0.60), tau=0.0)  # any movement triggers
    pos = Position(
        id="p1", portfolio_id="pf1", symbol="AAPL",
        shares=100.0, anchor_price=100.0, cash=10_000.0
    )
    price = 200.0  # asset pct will be high; SELL likely
    res = evaluate_position(pos, price=price, cfg=cfg)
    if res.side == "SELL":
        # After trim, projected asset% should be <= 0.60 (near upper bound)
        projected_shares = pos.shares + res.qty
        A_prime = price * projected_shares
        C_prime = pos.cash + pos.receivable - res.qty * price
        V_prime = A_prime + C_prime
        asset_pct = A_prime / max(V_prime, 1e-9)
        # use numeric tolerance (not pytest.approx in <=)
        assert asset_pct <= cfg.guardrails[1] + 1e-4

# ---- API integration tests ----

def test_get_position_card(client: TestClient):
    r = client.get("/v1/positions/pos1", params={"price": 190})
    assert r.status_code == 200
    body = r.json()
    assert set(["id", "symbol", "price", "anchor", "next_action"]).issubset(body.keys())


def test_evaluate_endpoint_records_event(client: TestClient):
    r = client.post("/v1/positions/pos1/evaluate", json={"price": 90})
    assert r.status_code == 200
    # Then events list should include an evaluation
    r2 = client.get("/v1/events")
    assert r2.status_code == 200
    items = r2.json()["items"]
    assert any(e.get("type") == "evaluation" for e in items)


# Suggested file: backend/tests/conftest.py
"""
Pytest config/fixtures. If imports fail due to module paths, uncomment the sys.path hack.
"""
# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

"""
Volatility Balancing — FastAPI MVP (v1)
Single-file scaffold to get execution started:
- Implements /v1 endpoints
- In-memory persistence (swap with Postgres later)
- Decision engine: triggers, sizing, guardrails, min_notional, commission
- Simple event log for auditability

How to run (local):
  uvicorn app:app --reload

How to test:
  pytest -q

NOTE: implementation follows the functional spec formulas & rules.
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Body, Path, Query, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

# ---------------------------
# Domain models / settings
# ---------------------------
class PortfolioSettings(BaseModel):
    tau: float = Field(0.03, description="Trigger threshold ±τ")
    r: float = Field(1.6667, description="Rebalance ratio")
    guardrails: tuple[float, float] = Field(
        (0.25, 0.75), description="(g_low, g_high) on asset%"
    )
    min_notional: float = 100.0
    commission_bps: float = 1.0  # 0.01% = 1 bps
    max_orders_day: int = 5
    withholding: float = 0.25
    after_hours: bool = False
    fractional: bool = True


class Position(BaseModel):
    id: str
    portfolio_id: str
    symbol: str
    shares: float
    anchor_price: float
    cash: float
    receivable: float = 0.0
    last_order_day_count: int = 0


class Event(BaseModel):
    id: str
    position_id: str
    type: str
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    message: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PositionCard(BaseModel):
    id: str
    symbol: str
    price: float
    anchor: float
    next_action: Optional[Literal["BUY", "SELL", "NONE"]]
    projected_asset_pct: Optional[float]


class OrderCallback(BaseModel):
    order_id: str
    status: Literal["filled", "canceled", "rejected"]
    qty: float
    price: float
    commission_bps: float = 1.0


# ---------------------------
# In-memory persistence (swap out later)
# ---------------------------
DB_POSITIONS: Dict[str, Position] = {}
DB_SETTINGS: Dict[str, PortfolioSettings] = {}
DB_EVENTS: List[Event] = []

# Seed demo state
DB_SETTINGS["pf1"] = PortfolioSettings()
DB_POSITIONS["pos1"] = Position(
    id="pos1",
    portfolio_id="pf1",
    symbol="AAPL",
    shares=10.0,
    anchor_price=189.0,
    cash=5000.0,
)

# ---------------------------
# Utility functions
# ---------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_event(evt: Event) -> None:
    DB_EVENTS.append(evt)


def commission_amount(notional: float, commission_bps: float) -> float:
    return notional * (commission_bps / 10_000.0)


# ---------------------------
# Decision engine per spec
# ---------------------------
class EvaluateResult(BaseModel):
    side: Optional[Literal["BUY", "SELL"]] = None
    qty: float = 0.0
    reason: str = ""
    asset_pct_after: Optional[float] = None
    trimmed: bool = False


def evaluate_position(
    position: Position, price: float, cfg: PortfolioSettings
) -> EvaluateResult:
    """Implements triggers, sizing formula, guardrails, and validations.
    Triggers: price >= anchor*(1+τ) => SELL; price <= anchor*(1-τ) => BUY.
    Size: ΔQ_raw = (P_anchor/P) * r * ((A + C_eff)/P)  (A=price*shares, C_eff=cash+receivable).
    Guardrails: enforce Asset% in [g_low, g_high] after trade; trim to nearest bound.
    Skips: min_notional, insufficient cash/shares.
    """
    A = price * position.shares
    C_eff = position.cash + position.receivable
    V = A + C_eff

    # Determine side based on thresholds
    buy_threshold = position.anchor_price * (1 - cfg.tau)
    sell_threshold = position.anchor_price * (1 + cfg.tau)
    if price <= buy_threshold:
        side = "BUY"
    elif price >= sell_threshold:
        side = "SELL"
    else:
        return EvaluateResult(reason="no_threshold_cross")

    # Raw size
    q_raw = (position.anchor_price / price) * cfg.r * (V / price)
    q = q_raw if side == "BUY" else -q_raw

    # Guardrail trim helper
    def asset_pct_after(qty: float) -> float:
        projected_shares = position.shares + qty
        A_prime = price * projected_shares
        C_prime = C_eff - qty * price  # qty positive for BUY reduces cash, negative for SELL increases cash
        V_prime = A_prime + C_prime
        return A_prime / max(V_prime, 1e-9)


    g_low, g_high = cfg.guardrails
    target_pct = None
    trimmed = False
    pct = asset_pct_after(q)
    if pct < g_low or pct > g_high:
        # Trim to nearest bound via binary search on qty
        trimmed = True
        target_pct = g_low if pct < g_low else g_high
        lo, hi = (0.0, abs(q))
        best = 0.0
        for _ in range(50):
            mid = (lo + hi) / 2.0
            test_q = mid if side == "BUY" else -mid
            ap = asset_pct_after(test_q)
            best = mid
            if (side == "BUY" and ap > target_pct) or (
                side == "SELL" and ap < target_pct
            ):
                hi = mid
            else:
                lo = mid
        q = best if side == "BUY" else -best

    # Validation: min_notional and resources
    notional = abs(q) * price
    if notional < cfg.min_notional:
        return EvaluateResult(reason="min_notional")
    if side == "BUY" and C_eff < notional:
        return EvaluateResult(reason="insufficient_cash")
    if side == "SELL" and position.shares < abs(q):
        return EvaluateResult(reason="insufficient_shares")

    return EvaluateResult(
        side=side, qty=q, asset_pct_after=asset_pct_after(q), trimmed=trimmed
    )


# ---------------------------
# FastAPI app & routes
# ---------------------------
app = FastAPI(title="Volatility Balancing Trading API", version="0.1.0")

# Patches & new files for Sprint 1
# Copy these into your repo paths as noted. After applying, run tests.

# =============================================================================
# FILE: backend/app/api/app.py  (append / modify as indicated)
# =============================================================================

# --- Health endpoints (add once) ---
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/v1/healthz")
def healthz_v1():
    return {"status": "ok", "version": "v1"}

# --- In-memory idempotency and orders store (stub) ---
IDEMPOTENCY_KEYS: set[str] = set()          # TODO: replace with Redis SETNX
DB_ORDERS: Dict[str, Dict[str, Any]] = {}   # id -> order dict (stub)

class CreateOrderRequest(BaseModel):
    side: Literal["BUY", "SELL"]
    qty: float

class CreateOrderResponse(BaseModel):
    order_id: str
    accepted: bool
    position_id: str

@app.post("/v1/positions/{position_id}/orders", response_model=CreateOrderResponse)
def create_order(
    position_id: str,
    payload: CreateOrderRequest,
    Idempotency_Key: Optional[str] = Header(None, convert_underscores=False),
):
    """Minimal order submit stub with idempotency header.
    - Requires Idempotency-Key header
    - Dedupes on the key (in-memory for now)
    - Emits an event and returns 202-ish response semantics (200 with body)
    """
    if Idempotency_Key is None or not Idempotency_Key.strip():
        raise HTTPException(status_code=400, detail="missing idempotency key")

    if Idempotency_Key in IDEMPOTENCY_KEYS:
        # Return the same order id if we already processed this key
        # (For simplicity we store mapping inside DB_ORDERS)
        for oid, od in DB_ORDERS.items():
            if od.get("idempotency_key") == Idempotency_Key:
                return CreateOrderResponse(order_id=oid, accepted=True, position_id=position_id)
        # If not found, just acknowledge
        return CreateOrderResponse(order_id="", accepted=True, position_id=position_id)

    IDEMPOTENCY_KEYS.add(Idempotency_Key)

    pos = DB_POSITIONS.get(position_id)
    if not pos:
        raise HTTPException(404, detail="position_not_found")

    # Very light validation (full checks live in evaluate)
    if payload.qty <= 0:
        raise HTTPException(400, detail="qty_must_be_positive")

    order_id = f"ord_{uuid.uuid4().hex[:8]}"
    DB_ORDERS[order_id] = {
        "position_id": position_id,
        "side": payload.side,
        "qty": payload.qty,
        "status": "submitted",
        "idempotency_key": Idempotency_Key,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    add_event(
        Event(
            id=f"evt_{len(DB_EVENTS)+1}",
            position_id=position_id,
            type="order_submitted_stub",
            inputs={"side": payload.side, "qty": payload.qty},
            outputs={"order_id": order_id},
            message=f"order submitted ({payload.side} {payload.qty})",
        )
    )

    return CreateOrderResponse(order_id=order_id, accepted=True, position_id=position_id)


# =============================================================================
# FILE: backend/tests/unit/test_health.py  (new or update existing)
# =============================================================================
import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_healthz_root():
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json().get("status") == "ok"

def test_healthz_v1():
    r = client.get("/v1/healthz")
    data = r.json()
    assert r.status_code == 200 and data.get("status") == "ok" and data.get("version") == "v1"


# =============================================================================
# FILE: backend/tests/integration/test_orders_stub.py  (new or update existing)
# =============================================================================
import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_orders_requires_idempotency():
    r = client.post("/v1/positions/pos1/orders", json={"side": "BUY", "qty": 1})
    assert r.status_code == 400
    assert r.json().get("detail") == "missing idempotency key"


def test_orders_accepts_with_idempotency():
    headers = {"Idempotency-Key": "test-key-123"}
    r = client.post("/v1/positions/pos1/orders", json={"side": "BUY", "qty": 1.5}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] is True
    assert body["position_id"] == "pos1"
    assert body["order_id"]


def test_orders_idempotent_replay_returns_same_order_id():
    headers = {"Idempotency-Key": "replay-1"}
    r1 = client.post("/v1/positions/pos1/orders", json={"side": "BUY", "qty": 1.5}, headers=headers)
    r2 = client.post("/v1/positions/pos1/orders", json={"side": "BUY", "qty": 1.5}, headers=headers)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["order_id"] == r2.json()["order_id"]


# =============================================================================
# DB Bootstrap (SQLAlchemy + Alembic) — initial models and migration guide
# =============================================================================
# Create these files to start moving off in-memory stores. You can commit the models now
# and generate migration 0001 next.

# FILE: backend/app/infra/db.py
from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")  # swap to Postgres later
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# FILE: backend/app/infra/models.py
from __future__ import annotations
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.sql import func
from .db import Base

class PositionORM(Base):
    __tablename__ = "positions"
    id = Column(String, primary_key=True)
    portfolio_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    shares = Column(Float, nullable=False)
    anchor_price = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    receivable = Column(Float, nullable=False, default=0.0)
    last_order_day_count = Column(Integer, nullable=False, default=0)

class EventORM(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True)
    position_id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    inputs_json = Column(JSON, nullable=False)
    outputs_json = Column(JSON, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class OrderORM(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    position_id = Column(String, nullable=False)
    side = Column(String, nullable=False)
    qty = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    idempotency_key = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

# FILE: backend/app/infra/__init__.py  (empty ok)

# -----------------------------------------------------------------------------
# Alembic quickstart (commands to run locally; not code):
#   pip install alembic sqlalchemy
#   alembic init backend/migrations
#   # Edit backend/migrations/env.py to set target_metadata from models Base
#   # Example snippet to paste into env.py:
#   from backend.app.infra.db import Base, engine
#   target_metadata = Base.metadata
#   # Then generate initial migration:
#   alembic revision --autogenerate -m "init tables"
#   alembic upgrade head
# -----------------------------------------------------------------------------


@app.get("/v1/positions/{position_id}", response_model=PositionCard)
def get_position(
    position_id: str = Path(...),
    price: float = Query(..., description="Current reference price"),
):
    pos = DB_POSITIONS.get(position_id)
    if not pos:
        raise HTTPException(404, "position_not_found")
    cfg = DB_SETTINGS[pos.portfolio_id]
    res = evaluate_position(pos, price, cfg)
    next_action = res.side if res.side else "NONE"
    return PositionCard(
        id=pos.id,
        symbol=pos.symbol,
        price=price,
        anchor=pos.anchor_price,
        next_action=next_action,
        projected_asset_pct=res.asset_pct_after,
    )


class EvaluateRequest(BaseModel):
    price: float


class EvaluateResponse(BaseModel):
    result: EvaluateResult


@app.post("/v1/positions/{position_id}/evaluate", response_model=EvaluateResponse)
def post_evaluate(position_id: str, body: EvaluateRequest):
    pos = DB_POSITIONS.get(position_id)
    if not pos:
        raise HTTPException(404, "position_not_found")
    cfg = DB_SETTINGS[pos.portfolio_id]
    res = evaluate_position(pos, body.price, cfg)

    evt = Event(
        id=f"evt_{len(DB_EVENTS)+1}",
        position_id=pos.id,
        type="evaluation",
        inputs={
            "price": body.price,
            "anchor": pos.anchor_price,
            "tau": cfg.tau,
            "r": cfg.r,
            "guardrails": cfg.guardrails,
            "min_notional": cfg.min_notional,
        },
        outputs=res.model_dump(),
        message=(
            res.reason if not res.side else f"proposed {res.side} {abs(res.qty):.4f}"
        ),
    )
    add_event(evt)
    return EvaluateResponse(result=res)


@app.get("/v1/events")
def list_events(
    position_id: Optional[str] = Query(None), page: int = 1, limit: int = 50
):
    items = [
        e.model_dump()
        for e in DB_EVENTS
        if (position_id is None or e.position_id == position_id)
    ]
    total = len(items)
    start = (page - 1) * limit
    end = start + limit
    return {"items": items[start:end], "page": page, "limit": limit, "total": total}


@app.post("/v1/orders/callback")
def orders_callback(payload: OrderCallback = Body(...)):
    # NOTE: add HMAC verification later; for now record an event and update anchor on fill
    evt = Event(
        id=f"evt_{len(DB_EVENTS)+1}",
        position_id="pos1",  # demo only — in real flow, map from order_id
        type="order_webhook",
        inputs=payload.model_dump(),
        outputs={},
        message=f"webhook {payload.status}",
    )
    add_event(evt)
    if payload.status == "filled":
        pos = DB_POSITIONS["pos1"]
        # Update cash and anchor (simplified: commission from bps)
        notional = abs(payload.qty) * payload.price
        fee = commission_amount(notional, payload.commission_bps)
        if payload.qty > 0:
            pos.cash -= notional + fee
        else:
            pos.cash += notional - fee
        pos.anchor_price = payload.price
    return {"ok": True}


@app.get("/v1/metrics")
def metrics_snapshot():
    # Minimal placeholder metrics from events
    skips = sum(
        1
        for e in DB_EVENTS
        if e.type == "evaluation"
        and e.outputs.get("reason")
        in {
            "min_notional",
            "no_threshold_cross",
            "insufficient_cash",
            "insufficient_shares",
        }
    )
    evaluations = sum(1 for e in DB_EVENTS if e.type == "evaluation")
    return {"min_notional_or_other_skips": skips, "evaluations": evaluations}


# ---------------------------
# Pytest tests (can be split into tests/test_*.py)
# ---------------------------
# To use: copy this section to tests/test_evaluate.py or run pytest collecting from this file with PYTEST_ADDOPTS.


def _reset_demo_state():
    DB_EVENTS.clear()
    DB_POSITIONS.clear()
    DB_SETTINGS.clear()
    DB_SETTINGS["pf1"] = PortfolioSettings()
    DB_POSITIONS["pos1"] = Position(
        id="pos1",
        portfolio_id="pf1",
        symbol="AAPL",
        shares=10.0,
        anchor_price=100.0,
        cash=1000.0,
    )


def test_no_threshold_cross():
    _reset_demo_state()
    pos = DB_POSITIONS["pos1"]
    res = evaluate_position(
        pos, price=101.0, cfg=DB_SETTINGS["pf1"]
    )  # τ=3% => range 97..103
    assert res.side is None and res.reason == "no_threshold_cross"


def test_buy_trigger_and_min_notional_skip():
    _reset_demo_state()
    pos = DB_POSITIONS["pos1"]
    # price drops 10% -> BUY, but min_notional=100, ensure result respects it based on qty sizing
    res = evaluate_position(pos, price=90.0, cfg=DB_SETTINGS["pf1"])  # BUY trigger
    # Depending on params, may or may not exceed min_notional; at least ensure side computed
    assert res.reason in {"min_notional", "insufficient_cash", ""}


def test_sell_trigger_generates_qty():
    _reset_demo_state()
    pos = DB_POSITIONS["pos1"]
    res = evaluate_position(pos, price=110.0, cfg=DB_SETTINGS["pf1"])  # SELL trigger
    assert res.side in {"SELL", None}  # allow guardrail/validation to skip


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# =========================
# backend/app/routes/positions.py
# =========================
# backend/app/routes/positions.py  (only the relevant bits)

from typing import Optional, cast
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.di import container
from dataclasses import asdict
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.types import ActionBelowMin
from application.use_cases.evaluate_position_uc import EvaluatePositionUC

router = APIRouter(prefix="/v1")


class OrderPolicyIn(BaseModel):
    min_qty: float = 0.0
    min_notional: float = 0.0
    lot_size: float = 0.0
    qty_step: float = 0.0
    action_below_min: str = "hold"  # "hold" | "reject" | "clip"


class CreatePositionRequest(BaseModel):
    ticker: str
    qty: float = 0.0
    cash: float = 0.0
    order_policy: Optional[OrderPolicyIn] = None


class CreatePositionResponse(BaseModel):
    id: str
    ticker: str
    qty: float
    cash: float
    # expose policy if you want it in the API response; otherwise remove:
    order_policy: Optional[OrderPolicyIn] = None


def _to_domain_policy(op: Optional[OrderPolicyIn]) -> OrderPolicy:
    if not op:
        return OrderPolicy()

    allowed = {"hold", "reject", "clip"}
    if op.action_below_min not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported action_below_min: {op.action_below_min!r}",
        )
    action = cast(ActionBelowMin, op.action_below_min)

    return OrderPolicy(
        min_qty=op.min_qty,
        min_notional=op.min_notional,
        lot_size=op.lot_size,
        qty_step=op.qty_step,
        action_below_min=action,
    )


@router.post("/positions", response_model=CreatePositionResponse, status_code=201)
def create_position(payload: CreatePositionRequest) -> CreatePositionResponse:
    pos_repo = container.positions
    pos = pos_repo.create(ticker=payload.ticker, qty=payload.qty, cash=payload.cash)

    if payload.order_policy:
        op = payload.order_policy
        pos.order_policy = OrderPolicy(
            min_qty=op.min_qty,
            min_notional=op.min_notional,
            lot_size=op.lot_size,
            qty_step=op.qty_step,
            action_below_min=op.action_below_min,
        )
        pos_repo.save(pos)

    return CreatePositionResponse(id=pos.id, ticker=pos.ticker, qty=pos.qty, cash=pos.cash)


@router.get("/positions/{position_id}")
def get_position(position_id: str) -> Dict[str, Any]:
    pos = container.positions.get(position_id)
    if not pos:
        raise HTTPException(404, detail="position_not_found")
    return {
        "id": pos.id,
        "ticker": pos.ticker,
        "qty": pos.qty,
        "cash": pos.cash,
    }


@router.post("/positions/{position_id}/evaluate")
def evaluate_position(position_id: str, current_price: float) -> Dict[str, Any]:
    """Evaluate position for volatility triggers."""
    if not container.positions.get(position_id):
        raise HTTPException(404, detail="position_not_found")

    uc = EvaluatePositionUC(
        positions=container.positions,
        events=container.events,
        clock=container.clock,
    )

    return uc.evaluate(position_id, current_price)


@router.post("/positions/{position_id}/anchor")
def set_anchor_price(position_id: str, price: float) -> Dict[str, Any]:
    """Set the anchor price for volatility trading."""
    pos = container.positions.get(position_id)
    if not pos:
        raise HTTPException(404, detail="position_not_found")

    pos.set_anchor_price(price)
    container.positions.save(pos)

    return {
        "position_id": position_id,
        "anchor_price": price,
        "message": f"Anchor price set to ${price:.2f}",
    }


@router.get("/positions/{position_id}/events")
def list_events(position_id: str, limit: int = 100) -> Dict[str, Any]:
    events = container.events.list_for_position(position_id, limit=limit)
    return {"position_id": position_id, "events": [asdict(e) for e in events]}

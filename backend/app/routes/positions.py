# =========================
# backend/app/routes/positions.py
# =========================
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dataclasses import asdict
from app.di import container

router = APIRouter(tags=["positions"])


class CreatePositionRequest(BaseModel):
    ticker: str
    qty: float = 0.0
    cash: float = 0.0


class CreatePositionResponse(BaseModel):
    id: str
    ticker: str
    qty: float
    cash: float


@router.post("/positions", response_model=CreatePositionResponse, status_code=201)
def create_position(payload: CreatePositionRequest):
    pos_repo = container.positions
    pos = pos_repo.create(ticker=payload.ticker, qty=payload.qty, cash=payload.cash)
    return CreatePositionResponse(id=pos.id, ticker=pos.ticker, qty=pos.qty, cash=pos.cash)


@router.get("/positions/{position_id}")
def get_position(position_id: str):
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
def evaluate_position(position_id: str):
    # Flow B placeholder: return empty proposals for now
    if not container.positions.get(position_id):
        raise HTTPException(404, detail="position_not_found")
    return {"position_id": position_id, "proposals": []}


@router.get("/positions/{position_id}/events")
def list_events(position_id: str, limit: int = 100):
    events = container.events.list_for_position(position_id, limit=limit)
    return {"position_id": position_id, "events": [asdict(e) for e in events]}

# backend/app/routes/orders.py
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header

from app.di import container
from application.dto.orders import (
    CreateOrderRequest,
    CreateOrderResponse,
    FillOrderRequest,
    FillOrderResponse,
)
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.use_cases.execute_order_uc import ExecuteOrderUC

router = APIRouter(tags=["orders"])


@router.post("/positions/{position_id}/orders", response_model=CreateOrderResponse)
def submit_order(
    position_id: str,
    payload: CreateOrderRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> CreateOrderResponse:
    uc = SubmitOrderUC(
        positions=container.positions,
        orders=container.orders,
        events=container.events,
        idempotency=container.idempotency,
        clock=container.clock,
    )
    # NOW: returns CreateOrderResponse directly
    return uc.execute(
        position_id=position_id,
        request=payload,
        idempotency_key=(idempotency_key or ""),
    )


@router.post("/orders/{order_id}/fill", response_model=FillOrderResponse)
def fill_order(order_id: str, payload: FillOrderRequest) -> FillOrderResponse:
    uc = ExecuteOrderUC(
        positions=container.positions,
        orders=container.orders,
        events=container.events,
        clock=container.clock,
    )
    try:
        return uc.execute(order_id=order_id, request=payload)
    except KeyError:
        # Normalize to HTTP 404 for missing order
        raise HTTPException(404, detail="order_not_found")


@router.get("/positions/{position_id}/orders")
def list_orders(position_id: str, limit: int = 100) -> Dict[str, Any]:
    if not container.positions.get(position_id):
        raise HTTPException(404, detail="position_not_found")
    orders = container.orders.list_for_position(position_id, limit=limit)
    return {"position_id": position_id, "orders": [asdict(o) for o in orders]}

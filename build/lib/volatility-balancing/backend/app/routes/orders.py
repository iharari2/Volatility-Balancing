# =========================
# backend/app/routes/orders.py
# =========================
from typing import Optional
from dataclasses import asdict
from fastapi import APIRouter, Header, HTTPException, Response, status

from app.di import container
from application.dto.orders import (
    CreateOrderRequest,
    CreateOrderResponse,
    FillOrderRequest,
    FillOrderResponse,
)
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.use_cases.execute_order_uc import ExecuteOrderUC
from domain.errors import IdempotencyConflict

router = APIRouter(tags=["orders"])


@router.post("/positions/{position_id}/orders", response_model=CreateOrderResponse, status_code=201)
def submit_order(
    position_id: str,
    payload: CreateOrderRequest,
    response: Response,  # non-default param before defaults
    idempotency_key: Optional[str] = Header(None),  # DEFAULT mapping underscores↔hyphens
):
    if idempotency_key is None or not idempotency_key.strip():
        raise HTTPException(400, detail="missing idempotency key")

    uc = SubmitOrderUC(
        positions=container.positions,
        orders=container.orders,
        idempotency=container.idempotency,
        events=container.events,
        clock=container.clock,
    )
    try:
        created, replay = uc.execute(
            position_id=position_id, request=payload, idempotency_key=idempotency_key
        )
    except IdempotencyConflict as e:
        raise HTTPException(409, detail=str(e))
    except KeyError:
        raise HTTPException(404, detail="position_not_found")

    # 201 on first create, 200 on replay
    if replay:
        response.status_code = status.HTTP_200_OK
        return CreateOrderResponse(
            order_id=created.order_id, accepted=True, position_id=position_id
        )
    response.status_code = status.HTTP_201_CREATED
    return CreateOrderResponse(order_id=created.order_id, accepted=True, position_id=position_id)


@router.post("/orders/{order_id}/fill", response_model=FillOrderResponse)
def fill_order(order_id: str, payload: FillOrderRequest):
    uc = ExecuteOrderUC(
        positions=container.positions,
        orders=container.orders,
        events=container.events,
        clock=container.clock,
    )
    try:
        result = uc.execute(order_id=order_id, request=payload)
    except KeyError:
        raise HTTPException(404, detail="order_not_found")
    return result


@router.get("/positions/{position_id}/orders")
def list_orders(position_id: str, limit: int = 100):
    # 404 if position doesn’t exist
    if not container.positions.get(position_id):
        raise HTTPException(404, detail="position_not_found")
    orders = container.orders.list_for_position(position_id, limit=limit)
    return {"position_id": position_id, "orders": [asdict(o) for o in orders]}

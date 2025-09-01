# backend/application/dto/orders.py
from __future__ import annotations
from pydantic import BaseModel
from domain.value_objects.types import OrderSide, OrderFillStatus


class CreateOrderRequest(BaseModel):
    side: OrderSide
    qty: float


class CreateOrderResponse(BaseModel):
    order_id: str
    accepted: bool
    position_id: str


class FillOrderRequest(BaseModel):
    qty: float
    price: float
    commission: float = 0.0


class FillOrderResponse(BaseModel):
    order_id: str
    status: OrderFillStatus
    filled_qty: float = 0.0

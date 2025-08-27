# =========================
# backend/application/dto/orders.py
# =========================
from typing import Literal
from pydantic import BaseModel, Field

class CreateOrderRequest(BaseModel):
    side: Literal["BUY", "SELL"]
    qty: float = Field(gt=0)

class CreateOrderResponse(BaseModel):
    order_id: str
    accepted: bool
    position_id: str

class FillOrderRequest(BaseModel):
    price: float = Field(gt=0)
    filled_qty: float = Field(gt=0)
    commission: float = Field(ge=0, default=0.0)

class FillOrderResponse(BaseModel):
    order_id: str
    status: str
    position_qty: float
    position_cash: float

class OrderProposal(BaseModel):
    side: Literal["BUY", "SELL"]
    qty: float
    rationale: str

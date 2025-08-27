from pydantic import BaseModel
from typing import Literal

class CreateOrderRequest(BaseModel):
    side: Literal["BUY", "SELL"]
    qty: float

class CreateOrderResponse(BaseModel):
    order_id: str
    accepted: bool
    position_id: str
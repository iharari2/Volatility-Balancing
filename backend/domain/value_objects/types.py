# File: backend/domain/value_objects/types.py
from typing import Literal

OrderSide = Literal["BUY", "SELL"]
OrderStatus = Literal["submitted", "filled", "rejected"]  # status stored on an Order
OrderFillStatus = Literal["filled", "skipped", "rejected"]  # status for a *fill* response
ActionBelowMin = Literal["hold", "reject", "clip"]

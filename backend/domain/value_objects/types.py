# File: backend/domain/value_objects/types.py
from typing import Literal

OrderSide = Literal["BUY", "SELL"]

# Extended OrderStatus to include broker workflow states
OrderStatus = Literal[
    "created",      # Initial state before submission
    "submitted",    # Submitted to our system
    "pending",      # Submitted to broker, awaiting acceptance
    "working",      # Accepted by broker, in the market
    "partial",      # Partially filled
    "filled",       # Completely filled
    "rejected",     # Rejected by broker or guardrails
    "cancelled",    # Cancelled by user or system
]

OrderFillStatus = Literal["filled", "skipped", "rejected"]  # status for a *fill* response
ActionBelowMin = Literal["hold", "reject", "clip"]

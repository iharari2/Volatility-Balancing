# =========================
# backend/domain/value_objects/position_state.py
# =========================
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class PositionState:
    """Position state value object for domain logic."""

    ticker: str
    qty: Decimal
    cash: Decimal
    dividend_receivable: Decimal
    anchor_price: Optional[Decimal] = None

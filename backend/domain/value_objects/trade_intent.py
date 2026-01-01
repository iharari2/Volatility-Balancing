# =========================
# backend/domain/value_objects/trade_intent.py
# =========================
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class TradeIntent:
    """Trade intent value object representing desired trade."""

    side: str  # "buy" | "sell"
    qty: Decimal  # desired quantity to trade
    reason: Optional[str] = None

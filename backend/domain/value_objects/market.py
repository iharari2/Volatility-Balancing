# =========================
# backend/domain/value_objects/market.py
# =========================
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class MarketQuote:
    """Market quote value object for domain logic."""

    ticker: str
    price: Decimal
    timestamp: datetime
    currency: str = "USD"

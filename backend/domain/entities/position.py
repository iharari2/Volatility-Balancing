# =========================
# backend/domain/entities/position.py
# =========================
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from domain.value_objects.guardrails import GuardrailPolicy
from domain.value_objects.order_policy import OrderPolicy


@dataclass
class Position:
    id: str
    ticker: str
    qty: float
    cash: float

    # Anchor price for volatility trading
    anchor_price: Optional[float] = None

    guardrails: GuardrailPolicy = field(default_factory=GuardrailPolicy)
    order_policy: OrderPolicy = field(default_factory=OrderPolicy)

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def set_anchor_price(self, price: float) -> None:
        """Set the anchor price for volatility trading."""
        self.anchor_price = price
        self.updated_at = datetime.now(timezone.utc)

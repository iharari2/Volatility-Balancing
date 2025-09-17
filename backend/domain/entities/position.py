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

    # Dividend-related fields
    dividend_receivable: float = 0.0  # Amount of dividend receivable
    withholding_tax_rate: float = 0.25  # Default 25% withholding tax

    guardrails: GuardrailPolicy = field(default_factory=GuardrailPolicy)
    order_policy: OrderPolicy = field(default_factory=OrderPolicy)

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def set_anchor_price(self, price: float) -> None:
        """Set the anchor price for volatility trading."""
        self.anchor_price = price
        self.updated_at = datetime.now(timezone.utc)

    def get_effective_cash(self) -> float:
        """Get effective cash including dividend receivable."""
        return self.cash + self.dividend_receivable

    def adjust_anchor_for_dividend(self, dividend_per_share: float) -> None:
        """Adjust anchor price for ex-dividend date."""
        if self.anchor_price is not None:
            self.anchor_price = self.anchor_price - dividend_per_share
            self.updated_at = datetime.now(timezone.utc)

    def add_dividend_receivable(self, amount: float) -> None:
        """Add dividend receivable amount."""
        self.dividend_receivable += amount
        self.updated_at = datetime.now(timezone.utc)

    def clear_dividend_receivable(self, amount: float) -> None:
        """Clear dividend receivable and add to cash."""
        self.dividend_receivable = max(0.0, self.dividend_receivable - amount)
        self.cash += amount
        self.updated_at = datetime.now(timezone.utc)

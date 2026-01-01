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
    tenant_id: str
    portfolio_id: str
    asset_symbol: str  # Renamed from ticker for clarity
    qty: float
    cash: float = 0.0  # Cash lives in PositionCell (per target state model)

    # Anchor price for volatility trading
    anchor_price: Optional[float] = None
    avg_cost: Optional[float] = None  # Average cost basis

    # Dividend-related fields
    dividend_receivable: float = 0.0  # Amount of dividend receivable
    withholding_tax_rate: float = 0.25  # Default 25% withholding tax

    # Commission and dividend aggregates (per spec)
    total_commission_paid: float = 0.0  # Cumulative commission paid
    total_dividends_received: float = 0.0  # Cumulative dividends received

    guardrails: GuardrailPolicy = field(default_factory=GuardrailPolicy)
    order_policy: OrderPolicy = field(default_factory=OrderPolicy)

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def set_anchor_price(self, price: float) -> None:
        """Set the anchor price for volatility trading."""
        self.anchor_price = price
        self.updated_at = datetime.now(timezone.utc)

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
        self.cash += amount  # Add cleared dividend to position cash
        self.updated_at = datetime.now(timezone.utc)

    def get_effective_cash(self) -> float:
        """Get effective cash including dividend receivable."""
        return self.cash + self.dividend_receivable

    def get_stock_value(self, current_price: Optional[float] = None) -> float:
        """
        Calculate stock value (qty * price).

        Args:
            current_price: Current market price. If None, uses anchor_price or avg_cost as fallback.

        Returns:
            Stock value (qty * price), or 0.0 if no price available.
        """
        price = current_price or self.anchor_price or self.avg_cost
        if price is None:
            return 0.0
        return self.qty * price

    def get_total_value(self, current_price: Optional[float] = None) -> float:
        """
        Calculate total position value (cash + stock value).

        Per Position Cell model: Each position is a self-contained trading cell
        combining cash and stock with independent strategy and performance measurement.

        Args:
            current_price: Current market price. If None, uses anchor_price or avg_cost as fallback.

        Returns:
            Total value (cash + stock value).
        """
        stock_value = self.get_stock_value(current_price)
        return self.cash + stock_value

    def get_allocation_pct(self, current_price: Optional[float] = None) -> dict[str, float]:
        """
        Calculate cash and stock allocation percentages.

        Args:
            current_price: Current market price. If None, uses anchor_price or avg_cost as fallback.

        Returns:
            Dictionary with 'cash_pct' and 'stock_pct' (0-100).
        """
        total_value = self.get_total_value(current_price)
        if total_value == 0:
            return {"cash_pct": 0.0, "stock_pct": 0.0}

        stock_value = self.get_stock_value(current_price)
        cash_pct = (self.cash / total_value) * 100
        stock_pct = (stock_value / total_value) * 100

        return {"cash_pct": cash_pct, "stock_pct": stock_pct}

    @property
    def ticker(self) -> str:
        """Backward compatibility: return asset_symbol as ticker."""
        return self.asset_symbol

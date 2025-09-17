# =========================
# backend/domain/entities/dividend.py
# =========================
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal


@dataclass
class Dividend:
    """Represents a dividend announcement and payment."""

    id: str
    ticker: str
    ex_date: datetime  # Ex-dividend date
    pay_date: datetime  # Payment date
    dps: Decimal  # Dividend per share
    currency: str = "USD"
    withholding_tax_rate: float = 0.25  # Default 25%
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def calculate_gross_amount(self, shares: float) -> Decimal:
        """Calculate gross dividend amount for given shares."""
        return Decimal(str(shares)) * self.dps

    def calculate_net_amount(self, shares: float) -> Decimal:
        """Calculate net dividend amount after withholding tax."""
        gross = self.calculate_gross_amount(shares)
        withholding = gross * Decimal(str(self.withholding_tax_rate))
        return gross - withholding

    def calculate_withholding_tax(self, shares: float) -> Decimal:
        """Calculate withholding tax amount."""
        gross = self.calculate_gross_amount(shares)
        return gross * Decimal(str(self.withholding_tax_rate))


@dataclass
class DividendReceivable:
    """Represents a dividend receivable for a position."""

    id: str
    position_id: str
    dividend_id: str
    shares_at_record: float  # Shares held on record date
    gross_amount: Decimal
    net_amount: Decimal
    withholding_tax: Decimal
    status: str = "pending"  # pending, paid, cancelled
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    paid_at: Optional[datetime] = None

    def mark_paid(self) -> None:
        """Mark the dividend as paid."""
        self.status = "paid"
        self.paid_at = datetime.now(timezone.utc)

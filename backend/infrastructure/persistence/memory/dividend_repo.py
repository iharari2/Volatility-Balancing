# =========================
# backend/infrastructure/persistence/memory/dividend_repo.py
# =========================
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict
from domain.entities.dividend import Dividend, DividendReceivable
from domain.ports.dividend_repo import DividendRepo, DividendReceivableRepo


class InMemoryDividendRepo(DividendRepo):
    """In-memory implementation of dividend repository."""

    def __init__(self):
        self._dividends: Dict[str, Dividend] = {}

    def create_dividend(self, dividend: Dividend) -> Dividend:
        """Create a new dividend record."""
        self._dividends[dividend.id] = dividend
        return dividend

    def get_dividend(self, dividend_id: str) -> Optional[Dividend]:
        """Get dividend by ID."""
        return self._dividends.get(dividend_id)

    def get_dividends_by_ticker(self, ticker: str) -> List[Dividend]:
        """Get all dividends for a ticker."""
        return [div for div in self._dividends.values() if div.ticker == ticker]

    def get_upcoming_dividends(self, ticker: str, from_date: datetime) -> List[Dividend]:
        """Get upcoming dividends for a ticker from a given date."""
        return [
            div
            for div in self._dividends.values()
            if div.ticker == ticker and div.ex_date >= from_date
        ]

    def get_dividend_by_ex_date(self, ticker: str, ex_date: datetime) -> Optional[Dividend]:
        """Get dividend by ticker and ex-date."""
        for div in self._dividends.values():
            if div.ticker == ticker and div.ex_date.date() == ex_date.date():
                return div
        return None


class InMemoryDividendReceivableRepo(DividendReceivableRepo):
    """In-memory implementation of dividend receivable repository."""

    def __init__(self):
        self._receivables: Dict[str, DividendReceivable] = {}

    def create_receivable(self, receivable: DividendReceivable) -> DividendReceivable:
        """Create a new dividend receivable record."""
        self._receivables[receivable.id] = receivable
        return receivable

    def get_receivable(self, receivable_id: str) -> Optional[DividendReceivable]:
        """Get dividend receivable by ID."""
        return self._receivables.get(receivable_id)

    def get_receivables_by_position(self, position_id: str) -> List[DividendReceivable]:
        """Get all receivables for a position."""
        return [rec for rec in self._receivables.values() if rec.position_id == position_id]

    def get_pending_receivables(self, position_id: str) -> List[DividendReceivable]:
        """Get pending receivables for a position."""
        return [
            rec
            for rec in self._receivables.values()
            if rec.position_id == position_id and rec.status == "pending"
        ]

    def update_receivable(self, receivable: DividendReceivable) -> DividendReceivable:
        """Update a dividend receivable record."""
        self._receivables[receivable.id] = receivable
        return receivable

    def mark_receivable_paid(self, receivable_id: str) -> Optional[DividendReceivable]:
        """Mark a receivable as paid."""
        receivable = self._receivables.get(receivable_id)
        if receivable:
            receivable.mark_paid()
        return receivable


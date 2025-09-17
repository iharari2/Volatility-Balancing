# =========================
# backend/domain/ports/dividend_repo.py
# =========================
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from domain.entities.dividend import Dividend, DividendReceivable


class DividendRepo(ABC):
    """Repository interface for dividend data."""

    @abstractmethod
    def create_dividend(self, dividend: Dividend) -> Dividend:
        """Create a new dividend record."""
        pass

    @abstractmethod
    def get_dividend(self, dividend_id: str) -> Optional[Dividend]:
        """Get dividend by ID."""
        pass

    @abstractmethod
    def get_dividends_by_ticker(self, ticker: str) -> List[Dividend]:
        """Get all dividends for a ticker."""
        pass

    @abstractmethod
    def get_upcoming_dividends(self, ticker: str, from_date: datetime) -> List[Dividend]:
        """Get upcoming dividends for a ticker from a given date."""
        pass

    @abstractmethod
    def get_dividend_by_ex_date(self, ticker: str, ex_date: datetime) -> Optional[Dividend]:
        """Get dividend by ticker and ex-date."""
        pass


class DividendReceivableRepo(ABC):
    """Repository interface for dividend receivable data."""

    @abstractmethod
    def create_receivable(self, receivable: DividendReceivable) -> DividendReceivable:
        """Create a new dividend receivable record."""
        pass

    @abstractmethod
    def get_receivable(self, receivable_id: str) -> Optional[DividendReceivable]:
        """Get dividend receivable by ID."""
        pass

    @abstractmethod
    def get_receivables_by_position(self, position_id: str) -> List[DividendReceivable]:
        """Get all receivables for a position."""
        pass

    @abstractmethod
    def get_pending_receivables(self, position_id: str) -> List[DividendReceivable]:
        """Get pending receivables for a position."""
        pass

    @abstractmethod
    def update_receivable(self, receivable: DividendReceivable) -> DividendReceivable:
        """Update a dividend receivable record."""
        pass

    @abstractmethod
    def mark_receivable_paid(self, receivable_id: str) -> Optional[DividendReceivable]:
        """Mark a receivable as paid."""
        pass


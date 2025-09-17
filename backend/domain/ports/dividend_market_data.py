# =========================
# backend/domain/ports/dividend_market_data.py
# =========================
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from domain.entities.dividend import Dividend


class DividendMarketDataRepo(ABC):
    """Repository interface for dividend market data."""

    @abstractmethod
    def get_dividend_info(self, ticker: str) -> Optional[Dividend]:
        """Get current dividend information for a ticker."""
        pass

    @abstractmethod
    def get_dividend_history(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> List[Dividend]:
        """Get dividend history for a ticker."""
        pass

    @abstractmethod
    def get_upcoming_dividends(self, ticker: str) -> List[Dividend]:
        """Get upcoming dividends for a ticker."""
        pass

    @abstractmethod
    def check_ex_dividend_today(self, ticker: str) -> Optional[Dividend]:
        """Check if today is ex-dividend date for a ticker."""
        pass


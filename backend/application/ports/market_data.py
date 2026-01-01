# =========================
# backend/application/ports/market_data.py
# =========================
from abc import ABC, abstractmethod
from datetime import datetime

from domain.value_objects.market import MarketQuote


class IMarketDataProvider(ABC):
    """Port for live market data."""

    @abstractmethod
    def get_latest_quote(self, ticker: str) -> MarketQuote:
        """Get the latest market quote for a ticker."""
        ...


class IHistoricalPriceProvider(ABC):
    """Port for historical market data."""

    @abstractmethod
    def get_quote_at(self, ticker: str, ts: datetime) -> MarketQuote:
        """Get historical market quote at a specific timestamp."""
        ...

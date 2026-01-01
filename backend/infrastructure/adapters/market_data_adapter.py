# =========================
# backend/infrastructure/adapters/market_data_adapter.py
# =========================
"""Adapter implementing IMarketDataProvider using existing MarketDataRepo."""

from application.ports.market_data import IMarketDataProvider
from domain.ports.market_data import MarketDataRepo
from domain.value_objects.market import MarketQuote
from infrastructure.adapters.converters import price_data_to_market_quote


class YFinanceMarketDataAdapter(IMarketDataProvider):
    """Adapter that implements IMarketDataProvider using existing YFinanceAdapter."""

    def __init__(self, market_data_repo: MarketDataRepo):
        """
        Initialize adapter with existing market data repository.

        Args:
            market_data_repo: Existing MarketDataRepo implementation (e.g., YFinanceAdapter)
        """
        self.market_data_repo = market_data_repo

    def get_latest_quote(self, ticker: str) -> MarketQuote:
        """Get the latest market quote for a ticker."""
        # Use get_reference_price which returns PriceData
        price_data = self.market_data_repo.get_reference_price(ticker)
        if price_data is None:
            raise ValueError(f"Could not fetch market data for {ticker}")

        return price_data_to_market_quote(price_data)

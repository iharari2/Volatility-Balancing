# =========================
# backend/infrastructure/adapters/historical_data_adapter.py
# =========================
"""Adapter implementing IHistoricalPriceProvider using stored historical data."""

from datetime import datetime

from application.ports.market_data import IHistoricalPriceProvider
from domain.ports.market_data import MarketDataRepo
from domain.value_objects.market import MarketQuote
from infrastructure.adapters.converters import price_data_to_market_quote


class HistoricalDataAdapter(IHistoricalPriceProvider):
    """Adapter that implements IHistoricalPriceProvider using historical data storage."""

    def __init__(self, market_data_repo: MarketDataRepo):
        """
        Initialize adapter with existing market data repository.

        Args:
            market_data_repo: Existing MarketDataRepo implementation (e.g., YFinanceAdapter)
        """
        self.market_data_repo = market_data_repo

    def get_quote_at(self, ticker: str, ts: datetime) -> MarketQuote:
        """Get historical market quote at a specific timestamp."""
        # For now, we'll use the current price from the repo
        # In a full implementation, this would query historical data storage
        # TODO: Implement proper historical data lookup from storage
        price_data = self.market_data_repo.get_reference_price(ticker)
        if price_data is None:
            raise ValueError(f"Could not fetch market data for {ticker} at {ts}")

        # Create MarketQuote with the requested timestamp
        # Note: In a real implementation, we'd fetch the actual price at that timestamp
        quote = price_data_to_market_quote(price_data)
        # Override timestamp with requested timestamp
        return MarketQuote(
            ticker=quote.ticker,
            price=quote.price,
            timestamp=ts,  # Use requested timestamp
            currency=quote.currency,
        )

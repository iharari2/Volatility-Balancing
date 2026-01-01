#!/usr/bin/env python3
"""
Mock market data adapter for fast testing.
This replaces the real YFinanceAdapter with synthetic data to eliminate API calls.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import random

from domain.ports.market_data import MarketDataRepo, MarketStatus
from domain.entities.market_data import PriceData, PriceSource, SimulationData


class MockMarketDataAdapter(MarketDataRepo):
    """Mock market data adapter that generates synthetic data for fast testing."""

    def __init__(self):
        self.tz_utc = timezone.utc
        self.tz_eastern = timezone.utc  # Simplified for testing
        self._price_cache = {}
        self._historical_cache = {}
        # Add storage attribute for compatibility
        self.storage = self

    def get_price(self, ticker: str) -> Optional[PriceData]:
        """Get current price data for a ticker."""
        if ticker not in self._price_cache:
            # Generate a realistic price based on ticker
            base_price = self._get_base_price(ticker)
            self._price_cache[ticker] = base_price

        price = self._price_cache[ticker]
        current_time = datetime.now(self.tz_utc)

        return PriceData(
            ticker=ticker,
            price=price,
            source=PriceSource.LAST_TRADE,
            timestamp=current_time,
            bid=price * 0.9995,  # Small spread
            ask=price * 1.0005,
            volume=1000000,
            last_trade_price=price,
            last_trade_time=current_time,
            is_market_hours=True,
            is_fresh=True,
            is_inline=True,
        )

    def get_market_status(self) -> MarketStatus:
        """Get current market status."""
        return MarketStatus(is_open=True, next_open=None, next_close=None, timezone="US/Eastern")

    def validate_price(
        self, price_data: PriceData, allow_after_hours: bool = False
    ) -> Dict[str, Any]:
        """Validate price data for trading decisions."""
        return {"valid": True, "warnings": [], "rejections": []}

    def get_reference_price(self, ticker: str) -> Optional[PriceData]:
        """Get reference price following the specification policy."""
        return self.get_price(ticker)

    def get_historical_data(
        self, ticker: str, start_date: datetime, end_date: datetime, market_hours_only: bool = False
    ) -> List[PriceData]:
        """Get historical price data for simulation and backtesting."""
        cache_key = f"{ticker}_{start_date}_{end_date}_{market_hours_only}"
        if cache_key in self._historical_cache:
            return self._historical_cache[cache_key]

        data = self._generate_historical_data(ticker, start_date, end_date, market_hours_only)
        self._historical_cache[cache_key] = data
        return data

    def get_trading_day_data(
        self, ticker: str, days: int = 5, include_after_hours: bool = False
    ) -> List[PriceData]:
        """Get data for last N trading days."""
        end = datetime.now(self.tz_utc)
        start = end - timedelta(days=days * 2)  # Account for weekends
        return self.get_historical_data(ticker, start, end, not include_after_hours)

    def get_volatility(self, ticker: str, window_minutes: int = 60) -> float:
        """Get volatility for a ticker."""
        return 0.02  # 2% volatility

    def get_simulation_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        include_after_hours: bool = False,
    ) -> SimulationData:
        """Get comprehensive data for simulation and backtesting."""
        price_data = self.get_historical_data(ticker, start_date, end_date, not include_after_hours)

        return SimulationData(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            price_data=price_data,
            daily_summaries=[],
            volatility_data=[],
            total_trading_days=len(price_data) // 13,  # Approximate trading days
            market_hours_data=price_data if not include_after_hours else [],
            after_hours_data=[] if not include_after_hours else price_data,
        )

    def fetch_historical_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        intraday_interval_minutes: int = 30,
    ) -> List[PriceData]:
        """Fetch historical data and store it."""
        data = self._generate_historical_data(
            ticker, start_date, end_date, True, intraday_interval_minutes
        )
        return data

    def _get_base_price(self, ticker: str) -> float:
        """Get a realistic base price for a ticker."""
        # Use deterministic but varied prices based on ticker
        hash_val = hash(ticker) % 1000
        base_prices = {
            "AAPL": 150.0,
            "MSFT": 300.0,
            "GOOGL": 2500.0,
            "TSLA": 200.0,
            "AMZN": 3000.0,
            "ZIM": 15.0,
        }
        return base_prices.get(ticker, 100.0 + (hash_val % 50))

    def _generate_historical_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        market_hours_only: bool = True,
        interval_minutes: int = 30,
    ) -> List[PriceData]:
        """Generate synthetic historical data."""
        base_price = self._get_base_price(ticker)
        price_data = []

        # Generate data points every interval_minutes during market hours
        current = start_date.replace(hour=9, minute=30, second=0, microsecond=0)
        # Use the actual end_date, not 16:00 on the same day
        end_time = end_date

        # Add some randomness but keep it deterministic
        random.seed(hash(ticker) + int(start_date.timestamp()))

        price = base_price
        while current <= end_time:
            # Skip weekends
            if current.weekday() < 5:  # Monday = 0, Friday = 4
                # Add some realistic price movement (smaller range for consistency)
                change_pct = random.uniform(-0.01, 0.01)  # ±1% max change
                price = price * (1 + change_pct)

                # Ensure price stays positive and reasonable
                price = max(base_price * 0.8, min(price, base_price * 1.2))

                spread = price * 0.001  # 0.1% spread

                price_data.append(
                    PriceData(
                        ticker=ticker,
                        price=price,
                        source=PriceSource.LAST_TRADE,
                        timestamp=current,
                        bid=price - spread / 2,
                        ask=price + spread / 2,
                        volume=random.randint(100000, 1000000),
                        last_trade_price=price,
                        last_trade_time=current,
                        is_market_hours=True,
                        is_fresh=True,
                        is_inline=True,
                        open=price * random.uniform(0.99, 1.01),
                        high=price * random.uniform(1.0, 1.02),
                        low=price * random.uniform(0.98, 1.0),
                        close=price,
                    )
                )

            # Move to next interval
            current += timedelta(minutes=interval_minutes)

        return price_data

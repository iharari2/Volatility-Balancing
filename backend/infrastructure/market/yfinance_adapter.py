# =========================
# backend/infrastructure/market/yfinance_adapter.py
# =========================
from __future__ import annotations
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import pytz

from domain.ports.market_data import MarketDataRepo, MarketStatus
from domain.entities.market_data import PriceData, PriceSource, SimulationData
from infrastructure.market.market_data_storage import MarketDataStorage


class YFinanceAdapter(MarketDataRepo):
    """yfinance implementation of market data repository with comprehensive storage."""

    def __init__(self):
        self.tz_eastern = pytz.timezone("US/Eastern")
        self.tz_utc = timezone.utc
        self.storage = MarketDataStorage()
        self.cache_ttl = 5  # 5 seconds cache TTL

    def get_price(self, ticker: str) -> Optional[PriceData]:
        """Get current price data for a ticker."""
        try:
            # Check storage cache first
            cached_data = self.storage.get_price_data(ticker)
            if cached_data and self._is_cache_valid(cached_data):
                return cached_data

            # Fetch fresh data
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1d", interval="1m")

            if hist.empty:
                return None

            # Get latest data
            latest = hist.iloc[-1]
            current_time = datetime.now(self.tz_utc)

            # Calculate mid-quote if bid/ask available
            bid = info.get("bid", latest["Low"])
            ask = info.get("ask", latest["High"])
            mid_quote = (bid + ask) / 2 if bid and ask else latest["Close"]

            # Determine price source following specification policy
            last_trade_price = latest["Close"]
            last_trade_time = latest.name.to_pydatetime().replace(tzinfo=self.tz_utc)

            # Reference price policy: Last trade if age ≤3s & within ±1% of mid
            age_seconds = (current_time - last_trade_time).total_seconds()
            price_diff_pct = abs(last_trade_price - mid_quote) / mid_quote if mid_quote > 0 else 1.0

            if age_seconds <= 3 and price_diff_pct <= 0.01:
                price = last_trade_price
                source = PriceSource.LAST_TRADE
                is_fresh = True
                is_inline = True
            else:
                price = mid_quote
                source = PriceSource.MID_QUOTE
                is_fresh = age_seconds <= 3
                is_inline = price_diff_pct <= 0.01

            # Check if market is open
            market_status = self.get_market_status()
            is_market_hours = market_status.is_open

            price_data = PriceData(
                ticker=ticker,
                price=price,
                source=source,
                timestamp=current_time,
                bid=bid,
                ask=ask,
                volume=int(latest["Volume"]) if not pd.isna(latest["Volume"]) else None,
                last_trade_price=last_trade_price,
                last_trade_time=last_trade_time,
                is_market_hours=bool(is_market_hours),
                is_fresh=bool(is_fresh),
                is_inline=bool(is_inline),
            )

            # Store in comprehensive storage system
            self.storage.store_price_data(ticker, price_data)

            return price_data

        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            return None

    def get_market_status(self) -> MarketStatus:
        """Get current market status."""
        try:
            # Get market calendar for today
            now_eastern = datetime.now(self.tz_eastern)
            today = now_eastern.date()

            # Market hours: 9:30 AM to 4:00 PM ET, Monday-Friday
            market_open = now_eastern.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now_eastern.replace(hour=16, minute=0, second=0, microsecond=0)

            # Check if it's a weekday
            is_weekday = now_eastern.weekday() < 5

            # Check if current time is within market hours
            is_open = is_weekday and market_open <= now_eastern <= market_close

            # Calculate next open/close
            next_open = None
            next_close = None

            if not is_open:
                if now_eastern < market_open and is_weekday:
                    # Market opens today
                    next_open = market_open
                    next_close = market_close
                else:
                    # Market closed, find next trading day
                    next_trading_day = self._get_next_trading_day(today)
                    next_open = self.tz_eastern.localize(
                        datetime.combine(
                            next_trading_day, datetime.min.time().replace(hour=9, minute=30)
                        )
                    )
                    next_close = self.tz_eastern.localize(
                        datetime.combine(
                            next_trading_day, datetime.min.time().replace(hour=16, minute=0)
                        )
                    )

            return MarketStatus(
                is_open=is_open, next_open=next_open, next_close=next_close, timezone="US/Eastern"
            )

        except Exception as e:
            print(f"Error getting market status: {e}")
            return MarketStatus(is_open=False, timezone="US/Eastern")

    def validate_price(
        self, price_data: PriceData, allow_after_hours: bool = False
    ) -> Dict[str, Any]:
        """Validate price data for trading decisions."""
        validation_result = {"valid": True, "warnings": [], "rejections": []}

        # Check if market is open (respect after-hours setting)
        if not price_data.is_market_hours:
            if not allow_after_hours:
                validation_result["valid"] = False
                validation_result["rejections"].append(
                    "Market is closed - after-hours trading disabled"
                )
            else:
                validation_result["warnings"].append("Trading after market hours")

        # Check if price is fresh (within 3 seconds)
        if not price_data.is_fresh:
            validation_result["warnings"].append("Price data is stale (>3 seconds old)")

        # Check if price is inline with mid-quote
        if not price_data.is_inline:
            validation_result["warnings"].append("Price deviates >1% from mid-quote")

        # Check for outlier prices (simplified - would need historical data for proper implementation)
        if price_data.price <= 0:
            validation_result["valid"] = False
            validation_result["rejections"].append("Invalid price (≤0)")

        # Check for extreme price movements (would need volatility calculation)
        # This is a simplified check - in production, you'd calculate 1-min volatility
        if price_data.price > 10000 or price_data.price < 0.01:
            validation_result["warnings"].append("Extreme price detected")

        return validation_result

    def get_reference_price(self, ticker: str) -> Optional[PriceData]:
        """Get reference price following the specification policy."""
        price_data = self.get_price(ticker)
        if not price_data:
            return None

        # Apply reference price policy from specification
        # Reference price: Last trade (if age ≤3s & within ±1% of mid); otherwise mid-quote
        if (
            price_data.source == PriceSource.LAST_TRADE
            and price_data.is_fresh
            and price_data.is_inline
        ):
            return price_data

        # If last trade doesn't meet criteria, use mid-quote
        if price_data.bid and price_data.ask:
            mid_price = (price_data.bid + price_data.ask) / 2
            return PriceData(
                ticker=ticker,
                price=mid_price,
                source=PriceSource.MID_QUOTE,
                timestamp=price_data.timestamp,
                bid=price_data.bid,
                ask=price_data.ask,
                volume=price_data.volume,
                last_trade_price=price_data.last_trade_price,
                last_trade_time=price_data.last_trade_time,
                is_market_hours=price_data.is_market_hours,
                is_fresh=price_data.is_fresh,
                is_inline=price_data.is_inline,
            )

        return price_data

    def _is_cache_valid(self, price_data: PriceData) -> bool:
        """Check if cached price data is still valid."""
        age_seconds = (datetime.now(self.tz_utc) - price_data.timestamp).total_seconds()
        return age_seconds < self.cache_ttl

    def get_historical_data(
        self, ticker: str, start_date: datetime, end_date: datetime, market_hours_only: bool = False
    ) -> List[PriceData]:
        """Get historical price data for simulation and backtesting."""
        return self.storage.get_historical_data(ticker, start_date, end_date, market_hours_only)

    def get_trading_day_data(
        self, ticker: str, days: int = 5, include_after_hours: bool = False
    ) -> List[PriceData]:
        """Get data for last N trading days."""
        return self.storage.get_trading_day_data(ticker, days, include_after_hours)

    def get_volatility(self, ticker: str, window_minutes: int = 60) -> float:
        """Get volatility for a ticker."""
        return self.storage.get_volatility(ticker, window_minutes)

    def get_simulation_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        include_after_hours: bool = False,
    ) -> SimulationData:
        """Get comprehensive data for simulation and backtesting."""
        return self.storage.get_simulation_data(ticker, start_date, end_date, include_after_hours)

    def fetch_historical_data(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> List[PriceData]:
        """Fetch historical data from yfinance and store it."""
        try:
            # Convert to yfinance format
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            # Determine appropriate interval based on date range
            days_diff = (end_date - start_date).days
            if days_diff <= 7:
                interval = "1m"  # 1-minute data for short periods (max 7 days)
            elif days_diff <= 60:
                interval = "1d"  # Daily data for medium periods (up to 60 days)
            else:
                interval = "1d"  # Daily data for long periods

            # Fetch data
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_str, end=end_str, interval=interval)

            if hist.empty:
                return []

            # Convert to PriceData objects
            price_data_list = []
            for timestamp, row in hist.iterrows():
                # Convert timestamp to UTC
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=self.tz_eastern).astimezone(self.tz_utc)
                else:
                    timestamp = timestamp.astimezone(self.tz_utc)

                # Calculate mid-quote
                mid_quote = (row["High"] + row["Low"]) / 2

                # Determine if market hours
                is_market_hours = self.storage.is_market_hours(timestamp)

                price_data = PriceData(
                    ticker=ticker,
                    price=row["Close"],
                    source=PriceSource.LAST_TRADE,
                    timestamp=timestamp,
                    bid=row["Low"],
                    ask=row["High"],
                    volume=int(row["Volume"]) if not pd.isna(row["Volume"]) else None,
                    last_trade_price=row["Close"],
                    last_trade_time=timestamp,
                    is_market_hours=bool(is_market_hours),
                    is_fresh=True,  # Historical data is considered fresh
                    is_inline=True,  # Historical data is considered inline
                )

                price_data_list.append(price_data)
                # Store in storage system
                self.storage.store_price_data(ticker, price_data)

            return price_data_list

        except Exception as e:
            print(f"Error fetching historical data for {ticker}: {e}")
            return []

    def _get_next_trading_day(self, date) -> datetime:
        """Get the next trading day (Monday-Friday)."""
        next_day = date + timedelta(days=1)
        while next_day.weekday() >= 5:  # Skip weekends
            next_day += timedelta(days=1)
        return next_day

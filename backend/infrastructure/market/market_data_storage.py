# =========================
# backend/infrastructure/market/market_data_storage.py
# =========================
from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz
import statistics
from collections import defaultdict

from domain.entities.market_data import PriceData, SimulationData, DailySummary, VolatilityData


class MarketDataStorage:
    """In-memory storage for market data with caching and retrieval capabilities."""

    def __init__(self):
        self.price_cache: Dict[str, PriceData] = {}
        self.historical_data: Dict[str, List[PriceData]] = defaultdict(list)
        self.tz_eastern = pytz.timezone("US/Eastern")
        self.tz_utc = pytz.UTC

    def store_price_data(self, ticker: str, price_data: PriceData) -> None:
        """Store price data for a ticker."""
        # Update cache
        self.price_cache[ticker] = price_data

        # Store in historical data (sorted by timestamp)
        if ticker not in self.historical_data:
            self.historical_data[ticker] = []

        # Insert in sorted order (most recent first)
        historical = self.historical_data[ticker]
        inserted = False
        for i, existing in enumerate(historical):
            if price_data.timestamp >= existing.timestamp:
                historical.insert(i, price_data)
                inserted = True
                break

        if not inserted:
            historical.append(price_data)

    def clear_price_cache(self, ticker: Optional[str] = None) -> None:
        """Clear cached price data for a ticker or all tickers."""
        if ticker:
            self.price_cache.pop(ticker, None)
        else:
            self.price_cache.clear()

    def get_price(self, ticker: str, force_refresh: bool = False) -> Optional[PriceData]:
        """Get the most recent price data for a ticker from cache.

        This implements the MarketDataRepo interface for simulation use.
        In simulation, data is pre-loaded via store_price_data().
        """
        return self.price_cache.get(ticker)

    def get_reference_price(self, ticker: str) -> Optional[PriceData]:
        """Get reference price - same as get_price for simulation."""
        return self.get_price(ticker)

    def validate_price(
        self, price_data: PriceData, allow_after_hours: bool = False
    ) -> dict:
        """Validate price data for trading decisions.

        For simulation, we always return valid since we're using historical data.
        """
        validation_result = {"valid": True, "warnings": [], "rejections": []}

        # Basic validation - reject invalid prices
        if price_data.price <= 0:
            validation_result["valid"] = False
            validation_result["rejections"].append("Invalid price (≤0)")

        # In simulation, we allow after-hours by default since we control the data
        # Only reject if explicitly not allowed AND price is marked as after-hours
        if not price_data.is_market_hours and not allow_after_hours:
            # For simulation, just add a warning but don't reject
            validation_result["warnings"].append("After-hours price point")

        return validation_result

    def get_market_status(self):
        """Get market status - for simulation, market is always open."""
        from domain.ports.market_data import MarketStatus
        return MarketStatus(is_open=True)

    def get_historical_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        market_hours_only: bool = False,
    ) -> List[PriceData]:
        """Get historical price data for a ticker within a date range."""
        if ticker not in self.historical_data:
            return []

        # Ensure dates are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=self.tz_utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=self.tz_utc)

        historical = self.historical_data[ticker]
        result = []

        for price_data in historical:
            # Check if within date range
            if start_date <= price_data.timestamp <= end_date:
                # Filter by market hours if requested
                if market_hours_only and not price_data.is_market_hours:
                    continue
                result.append(price_data)

        # Return in chronological order (oldest first)
        result.sort(key=lambda x: x.timestamp)
        return result

    def get_trading_day_data(
        self, ticker: str, days: int = 5, include_after_hours: bool = False
    ) -> List[PriceData]:
        """Get data for last N trading days."""
        if ticker not in self.historical_data:
            return []

        historical = self.historical_data[ticker]
        if not historical:
            return []

        # Get most recent data
        end_date = historical[0].timestamp
        start_date = end_date - timedelta(days=days * 2)  # Get extra days to account for weekends

        result = self.get_historical_data(ticker, start_date, end_date, market_hours_only=False)

        # Filter to only market hours if requested
        if not include_after_hours:
            result = [pd for pd in result if pd.is_market_hours]

        # Group by trading day and take last N days
        trading_days = {}
        for price_data in result:
            day_key = price_data.timestamp.date()
            if day_key not in trading_days:
                trading_days[day_key] = []
            trading_days[day_key].append(price_data)

        # Get last N trading days
        sorted_days = sorted(trading_days.keys(), reverse=True)[:days]
        final_result = []
        for day in sorted_days:
            final_result.extend(trading_days[day])

        # Sort chronologically
        final_result.sort(key=lambda x: x.timestamp)
        return final_result

    def get_volatility(self, ticker: str, window_minutes: int = 60) -> float:
        """Get volatility for a ticker over a time window."""
        if ticker not in self.historical_data:
            return 0.0

        historical = self.historical_data[ticker]
        if len(historical) < 2:
            return 0.0

        # Get data within the window
        end_time = historical[0].timestamp
        start_time = end_time - timedelta(minutes=window_minutes)

        window_data = [
            pd for pd in historical if start_time <= pd.timestamp <= end_time and pd.is_market_hours
        ]

        if len(window_data) < 2:
            return 0.0

        # Calculate returns
        returns = []
        for i in range(1, len(window_data)):
            prev_price = window_data[i - 1].price
            curr_price = window_data[i].price
            if prev_price > 0:
                ret = (curr_price - prev_price) / prev_price
                returns.append(ret)

        if not returns:
            return 0.0

        # Calculate standard deviation of returns
        if len(returns) < 2:
            return 0.0

        mean_return = statistics.mean(returns)
        variance = statistics.variance(returns, mean_return) if len(returns) > 1 else 0.0
        volatility = variance**0.5

        # Annualize (assuming 252 trading days, 390 minutes per day)
        minutes_per_year = 252 * 390
        annualized_volatility = volatility * (minutes_per_year / window_minutes) ** 0.5

        return annualized_volatility

    def get_simulation_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        include_after_hours: bool = False,
    ) -> SimulationData:
        """Get comprehensive data for simulation and backtesting."""
        # Get price data
        price_data = self.get_historical_data(ticker, start_date, end_date, market_hours_only=False)

        # Filter by market hours if needed
        market_hours_data = [pd for pd in price_data if pd.is_market_hours]
        after_hours_data = [pd for pd in price_data if not pd.is_market_hours]

        if not include_after_hours:
            price_data = market_hours_data

        # Calculate daily summaries
        daily_summaries = self._calculate_daily_summaries(price_data)

        # Calculate volatility data
        volatility_data = self._calculate_volatility_data(price_data)

        # Count trading days
        trading_days = len(set(pd.timestamp.date() for pd in market_hours_data))

        return SimulationData(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            price_data=price_data,
            daily_summaries=daily_summaries,
            volatility_data=volatility_data,
            total_trading_days=trading_days,
            market_hours_data=market_hours_data,
            after_hours_data=after_hours_data,
        )

    def _calculate_daily_summaries(self, price_data: List[PriceData]) -> List[DailySummary]:
        """Calculate daily summaries from price data."""
        from collections import defaultdict

        daily_data = defaultdict(list)
        for pd in price_data:
            day_key = pd.timestamp.date()
            daily_data[day_key].append(pd)

        summaries = []
        for day, data_points in sorted(daily_data.items()):
            if not data_points:
                continue

            prices = [dp.price for dp in data_points]
            volumes = [dp.volume for dp in data_points if dp.volume]

            # Get OHLC from first/last/high/low
            open_price = data_points[0].open or data_points[0].price
            close_price = data_points[-1].close or data_points[-1].price
            high_price = max(prices)
            low_price = min(prices)
            volume = sum(volumes) if volumes else None

            # Calculate VWAP and volatility for DailySummary
            # VWAP = sum(price * volume) / sum(volume)
            total_value = sum(pd.price * (pd.volume or 0) for pd in data_points)
            total_volume = sum(pd.volume or 0 for pd in data_points)
            vwap = total_value / total_volume if total_volume > 0 else close_price

            # Simple volatility calculation: std dev of prices
            import statistics

            prices_list = [pd.price for pd in data_points]
            volatility = statistics.stdev(prices_list) if len(prices_list) > 1 else 0.0

            summary = DailySummary(
                ticker=data_points[0].ticker,
                date=datetime.combine(day, datetime.min.time()).replace(tzinfo=self.tz_utc),
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume or 0,
                vwap=vwap,
                volatility=volatility,
            )
            summaries.append(summary)

        return summaries

    def _calculate_volatility_data(self, price_data: List[PriceData]) -> List[VolatilityData]:
        """Calculate volatility data from price data."""
        if len(price_data) < 2:
            return []

        # Group by day
        daily_data = defaultdict(list)
        for pd in price_data:
            day_key = pd.timestamp.date()
            daily_data[day_key].append(pd)

        volatility_list = []
        for day, data_points in sorted(daily_data.items()):
            if len(data_points) < 2:
                continue

            prices = [dp.price for dp in data_points]
            returns = []
            for i in range(1, len(prices)):
                if prices[i - 1] > 0:
                    ret = (prices[i] - prices[i - 1]) / prices[i - 1]
                    returns.append(ret)

            if not returns:
                continue

            mean_return = statistics.mean(returns)
            variance = statistics.variance(returns, mean_return) if len(returns) > 1 else 0.0
            volatility = variance**0.5

            volatility_data = VolatilityData(
                ticker=data_points[0].ticker,
                timestamp=datetime.combine(day, datetime.min.time()).replace(tzinfo=self.tz_utc),
                volatility_1min=volatility,  # Using calculated volatility for 1min
                volatility_5min=volatility,  # Using same value for 5min (can be improved)
                volatility_1hour=volatility,  # Using calculated volatility for 1hour (window_minutes=60)
                price_std_dev=volatility,  # Using volatility as std dev
                sample_size=len(returns),
            )
            volatility_list.append(volatility_data)

        return volatility_list

    def is_market_hours(self, timestamp: datetime) -> bool:
        """Check if a timestamp is during market hours."""
        # Ensure timestamp is timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=self.tz_utc)

        # Convert to Eastern time
        et_time = timestamp.astimezone(self.tz_eastern)

        # Check if weekday (Monday=0, Friday=4)
        if et_time.weekday() >= 5:  # Saturday or Sunday
            return False

        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = et_time.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = et_time.replace(hour=16, minute=0, second=0, microsecond=0)

        return market_open <= et_time <= market_close

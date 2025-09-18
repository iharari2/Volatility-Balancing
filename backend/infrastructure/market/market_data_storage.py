# =========================
# backend/infrastructure/market/market_data_storage.py
# =========================
from __future__ import annotations
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import pytz

from domain.entities.market_data import PriceData, DailySummary, VolatilityData, SimulationData


class MarketDataStorage:
    """Comprehensive market data storage with retention policies."""

    def __init__(self):
        # Data retention policies
        self.REAL_TIME_CACHE_TTL = 5  # seconds
        self.HISTORICAL_DATA_HOURS = 24 * 7  # 7 days for simulations
        self.DAILY_SUMMARIES_DAYS = 365  # days
        self.VOLATILITY_CACHE_MINUTES = 60  # minutes

        # Storage layers
        self.price_cache: Dict[str, PriceData] = {}
        self.price_history: Dict[str, List[PriceData]] = {}
        self.daily_summaries: Dict[str, List[DailySummary]] = {}
        self.volatility_cache: Dict[str, VolatilityData] = {}

        # Market calendar
        self.tz_eastern = pytz.timezone("US/Eastern")
        self.tz_utc = timezone.utc

        # Market holidays (simplified - in production, use a proper calendar)
        self.market_holidays = self._get_market_holidays()

    def store_price_data(self, ticker: str, price_data: PriceData) -> None:
        """Store price data in appropriate storage layers."""
        # Update real-time cache
        self.price_cache[ticker] = price_data

        # Add to historical data
        if ticker not in self.price_history:
            self.price_history[ticker] = []

        self.price_history[ticker].append(price_data)

        # Clean up old historical data (temporarily disabled for testing)
        # self._cleanup_historical_data(ticker)

        # Update volatility cache if needed
        self._update_volatility_cache(ticker)

    def get_price_data(self, ticker: str) -> Optional[PriceData]:
        """Get latest price data from cache."""
        return self.price_cache.get(ticker)

    def get_historical_data(
        self,
        ticker: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        market_hours_only: bool = False,
    ) -> List[PriceData]:
        """Get historical price data for a ticker."""
        if ticker not in self.price_history:
            return []

        data = self.price_history[ticker]

        # Filter by time range with proper timezone handling
        if start_time:
            # Ensure timezone-aware comparison
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            data = [p for p in data if p.timestamp >= start_time]
        if end_time:
            # Ensure timezone-aware comparison
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            data = [p for p in data if p.timestamp <= end_time]

        # Filter by market hours
        if market_hours_only:
            data = [p for p in data if p.is_market_hours]

        return sorted(data, key=lambda x: x.timestamp)

    def get_trading_day_data(
        self, ticker: str, days: int = 5, include_after_hours: bool = False
    ) -> List[PriceData]:
        """Get data for last N trading days."""
        if ticker not in self.price_history:
            return []

        # Calculate start date (N trading days ago)
        start_date = self._get_trading_days_ago(days)

        # Get data from start date
        data = self.get_historical_data(ticker, start_time=start_date)

        # Filter by market hours if needed
        if not include_after_hours:
            data = [p for p in data if p.is_market_hours]

        return data

    def get_volatility(self, ticker: str, window_minutes: int = 60) -> float:
        """Calculate rolling volatility for a ticker."""
        if ticker not in self.volatility_cache:
            return 0.0

        vol_data = self.volatility_cache[ticker]

        # Return appropriate volatility based on window
        if window_minutes <= 5:
            return vol_data.volatility_5min
        elif window_minutes <= 60:
            return vol_data.volatility_1hour
        else:
            return vol_data.volatility_1hour  # Default to 1-hour

    def get_daily_summary(self, ticker: str, date: datetime) -> Optional[DailySummary]:
        """Get daily summary for a ticker on a specific date."""
        if ticker not in self.daily_summaries:
            return None

        date_str = date.date().isoformat()
        for summary in self.daily_summaries[ticker]:
            if summary.date.date().isoformat() == date_str:
                return summary

        return None

    def get_simulation_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        include_after_hours: bool = False,
    ) -> SimulationData:
        """Get comprehensive data for simulation and backtesting."""
        # Get price data
        price_data = self.get_historical_data(ticker, start_date, end_date)

        # Separate market hours and after-hours data
        market_hours_data = [p for p in price_data if p.is_market_hours]
        after_hours_data = [p for p in price_data if not p.is_market_hours]

        # Get daily summaries
        daily_summaries = []
        current_date = start_date.date()
        end_date_only = end_date.date()

        while current_date <= end_date_only:
            summary = self.get_daily_summary(
                ticker, datetime.combine(current_date, datetime.min.time())
            )
            if summary:
                daily_summaries.append(summary)
            current_date += timedelta(days=1)

        # Get volatility data
        volatility_data = []
        if ticker in self.volatility_cache:
            vol_data = self.volatility_cache[ticker]
            # Ensure timezone-aware comparison
            vol_timestamp = vol_data.timestamp
            if vol_timestamp.tzinfo is None:
                vol_timestamp = vol_timestamp.replace(tzinfo=timezone.utc)
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            if start_date <= vol_timestamp <= end_date:
                volatility_data.append(vol_data)

        # Calculate total trading days based on actual price data
        # Count unique trading days from price data
        trading_days = set()
        for price_point in price_data:
            trading_days.add(price_point.timestamp.date())
        total_trading_days = len(trading_days)

        return SimulationData(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            price_data=price_data,
            daily_summaries=daily_summaries,
            volatility_data=volatility_data,
            total_trading_days=total_trading_days,
            market_hours_data=market_hours_data,
            after_hours_data=after_hours_data,
        )

    def is_trading_day(self, date: datetime) -> bool:
        """Check if date is a trading day (weekday, not holiday)."""
        if date.weekday() >= 5:  # Weekend
            return False

        # Check for holidays
        date_only = date.date()
        return date_only not in self.market_holidays

    def is_market_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is during market hours."""
        # Convert to Eastern time
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=self.tz_utc)

        et_time = timestamp.astimezone(self.tz_eastern)

        # Check if it's a trading day
        if not self.is_trading_day(et_time):
            return False

        # Check if it's within market hours (9:30 AM - 4:00 PM ET)
        market_open = et_time.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = et_time.replace(hour=16, minute=0, second=0, microsecond=0)

        return market_open <= et_time <= market_close

    def _cleanup_historical_data(self, ticker: str) -> None:
        """Clean up old historical data based on retention policy."""
        if ticker not in self.price_history:
            return

        cutoff_time = datetime.now(self.tz_utc) - timedelta(hours=self.HISTORICAL_DATA_HOURS)
        self.price_history[ticker] = [
            p for p in self.price_history[ticker] if p.timestamp > cutoff_time
        ]

    def _update_volatility_cache(self, ticker: str) -> None:
        """Update volatility cache for a ticker."""
        if ticker not in self.price_history:
            return

        data = self.price_history[ticker]
        if len(data) < 2:
            return

        # Calculate volatilities for different windows
        prices = [p.price for p in data]

        # 1-minute volatility (last 60 data points)
        vol_1min = self._calculate_volatility(prices[-60:]) if len(prices) >= 60 else 0.0

        # 5-minute volatility (last 300 data points)
        vol_5min = self._calculate_volatility(prices[-300:]) if len(prices) >= 300 else 0.0

        # 1-hour volatility (last 3600 data points)
        vol_1hour = self._calculate_volatility(prices[-3600:]) if len(prices) >= 3600 else 0.0

        # Standard deviation
        price_std = statistics.stdev(prices) if len(prices) > 1 else 0.0

        self.volatility_cache[ticker] = VolatilityData(
            ticker=ticker,
            timestamp=datetime.now(self.tz_utc),
            volatility_1min=vol_1min,
            volatility_5min=vol_5min,
            volatility_1hour=vol_1hour,
            price_std_dev=price_std,
            sample_size=len(prices),
        )

    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate volatility from price series."""
        if len(prices) < 2:
            return 0.0

        # Calculate returns
        returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]

        # Calculate standard deviation of returns
        if len(returns) < 2:
            return 0.0

        return statistics.stdev(returns)

    def _get_trading_days_ago(self, days: int) -> datetime:
        """Get datetime N trading days ago."""
        current_date = datetime.now(self.tz_eastern).date()
        trading_days_count = 0
        check_date = current_date

        while trading_days_count < days:
            check_date -= timedelta(days=1)
            if self.is_trading_day(datetime.combine(check_date, datetime.min.time())):
                trading_days_count += 1

        return datetime.combine(check_date, datetime.min.time()).replace(tzinfo=self.tz_eastern)

    def _get_market_holidays(self) -> List[datetime]:
        """Get list of market holidays (simplified)."""
        # In production, use a proper market calendar like pandas_market_calendars
        current_year = datetime.now().year
        holidays = []

        # New Year's Day
        holidays.append(datetime(current_year, 1, 1).date())

        # Martin Luther King Jr. Day (3rd Monday in January)
        mlk_day = self._get_nth_weekday(current_year, 1, 0, 3)  # Monday = 0
        holidays.append(mlk_day)

        # Presidents' Day (3rd Monday in February)
        presidents_day = self._get_nth_weekday(current_year, 2, 0, 3)
        holidays.append(presidents_day)

        # Good Friday (simplified - would need proper calculation)
        # Independence Day
        holidays.append(datetime(current_year, 7, 4).date())

        # Labor Day (1st Monday in September)
        labor_day = self._get_nth_weekday(current_year, 9, 0, 1)
        holidays.append(labor_day)

        # Thanksgiving (4th Thursday in November)
        thanksgiving = self._get_nth_weekday(current_year, 11, 3, 4)  # Thursday = 3
        holidays.append(thanksgiving)

        # Christmas Day
        holidays.append(datetime(current_year, 12, 25).date())

        return holidays

    def _get_nth_weekday(self, year: int, month: int, weekday: int, n: int) -> datetime:
        """Get the nth weekday of a month."""
        first_day = datetime(year, month, 1)
        first_weekday = (weekday - first_day.weekday()) % 7
        target_day = first_day + timedelta(days=first_weekday + (n - 1) * 7)
        return target_day.date()

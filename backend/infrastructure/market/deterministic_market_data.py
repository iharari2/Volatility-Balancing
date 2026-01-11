from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from domain.ports.market_data import MarketDataRepo, MarketStatus
from domain.entities.market_data import PriceData, PriceSource, SimulationData


class DeterministicMarketDataAdapter(MarketDataRepo):
    """Deterministic market data adapter for local verification without network."""

    def __init__(
        self,
        base_prices: Optional[Dict[str, float]] = None,
        multipliers: Optional[List[float]] = None,
    ) -> None:
        self._base_prices = base_prices or {
            "AAPL": 100.0,
            "MSFT": 200.0,
            "GOOGL": 150.0,
            "TSLA": 180.0,
            "AMZN": 120.0,
            "ZIM": 15.0,
        }
        # Default sequence guarantees >=1 BUY and >=1 SELL within 10 ticks
        self._multipliers = multipliers or [
            1.00,
            1.04,
            1.01,
            0.96,
            1.00,
            1.04,
            0.98,
            1.00,
            1.04,
            0.96,
        ]
        self._indices: Dict[str, int] = {}
        self._last_price: Dict[str, float] = {}
        self._last_timestamp: Dict[str, datetime] = {}
        self._start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        # For compatibility with code that expects a storage attribute
        self.storage = self

    def clear_cache(self, ticker: Optional[str] = None) -> None:
        """Reset deterministic sequence state."""
        if ticker:
            self._indices.pop(ticker, None)
            self._last_price.pop(ticker, None)
            self._last_timestamp.pop(ticker, None)
            return
        self._indices.clear()
        self._last_price.clear()
        self._last_timestamp.clear()

    def _get_base_price(self, ticker: str) -> float:
        return self._base_prices.get(ticker.upper(), 100.0)

    def _get_sequence(self, ticker: str) -> List[float]:
        base_price = self._get_base_price(ticker)
        return [base_price * mult for mult in self._multipliers]

    def _advance_price(self, ticker: str) -> PriceData:
        index = self._indices.get(ticker, 0)
        sequence = self._get_sequence(ticker)
        price = sequence[index % len(sequence)]
        timestamp = self._start_time + timedelta(seconds=index)
        self._indices[ticker] = index + 1
        self._last_price[ticker] = price
        self._last_timestamp[ticker] = timestamp
        spread = price * 0.002
        return PriceData(
            ticker=ticker,
            price=price,
            source=PriceSource.MID_QUOTE,
            timestamp=timestamp,
            bid=price - spread / 2,
            ask=price + spread / 2,
            volume=1_000_000,
            last_trade_price=price,
            last_trade_time=timestamp,
            is_market_hours=True,
            is_fresh=True,
            is_inline=True,
        )

    def get_price(self, ticker: str, force_refresh: bool = False) -> Optional[PriceData]:
        """Return last deterministic price without advancing the sequence."""
        if ticker not in self._last_price or force_refresh:
            return self._advance_price(ticker)
        price = self._last_price[ticker]
        timestamp = self._last_timestamp[ticker]
        spread = price * 0.002
        return PriceData(
            ticker=ticker,
            price=price,
            source=PriceSource.MID_QUOTE,
            timestamp=timestamp,
            bid=price - spread / 2,
            ask=price + spread / 2,
            volume=1_000_000,
            last_trade_price=price,
            last_trade_time=timestamp,
            is_market_hours=True,
            is_fresh=True,
            is_inline=True,
        )

    def get_reference_price(self, ticker: str) -> Optional[PriceData]:
        """Advance deterministic sequence for the next tick."""
        return self._advance_price(ticker)

    def get_market_status(self) -> MarketStatus:
        return MarketStatus(is_open=True, next_open=None, next_close=None, timezone="US/Eastern")

    def validate_price(
        self, price_data: PriceData, allow_after_hours: bool = False
    ) -> Dict[str, Any]:
        return {"valid": True, "warnings": [], "rejections": []}

    def get_historical_data(
        self, ticker: str, start_date: datetime, end_date: datetime, market_hours_only: bool = False
    ) -> List[PriceData]:
        return self._generate_historical_data(ticker, start_date, end_date, interval_minutes=30)

    def fetch_historical_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        intraday_interval_minutes: int = 30,
    ) -> List[PriceData]:
        return self._generate_historical_data(
            ticker, start_date, end_date, interval_minutes=intraday_interval_minutes
        )

    def get_trading_day_data(
        self, ticker: str, days: int = 5, include_after_hours: bool = False
    ) -> List[PriceData]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        return self._generate_historical_data(ticker, start, end, interval_minutes=60)

    def get_volatility(self, ticker: str, window_minutes: int = 60) -> float:
        return 0.02

    def get_simulation_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        include_after_hours: bool = False,
    ) -> SimulationData:
        price_data = self._generate_historical_data(ticker, start_date, end_date, interval_minutes=60)
        return SimulationData(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            price_data=price_data,
            daily_summaries=[],
            volatility_data=[],
            total_trading_days=len(price_data) // 13 if price_data else 0,
            market_hours_data=price_data if not include_after_hours else [],
            after_hours_data=price_data if include_after_hours else [],
        )

    def _generate_historical_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval_minutes: int = 30,
    ) -> List[PriceData]:
        if start_date >= end_date:
            return []
        data: List[PriceData] = []
        sequence = self._get_sequence(ticker)
        idx = 0
        current = start_date
        while current <= end_date:
            price = sequence[idx % len(sequence)]
            spread = price * 0.002
            data.append(
                PriceData(
                    ticker=ticker,
                    price=price,
                    source=PriceSource.MID_QUOTE,
                    timestamp=current,
                    bid=price - spread / 2,
                    ask=price + spread / 2,
                    volume=1_000_000,
                    last_trade_price=price,
                    last_trade_time=current,
                    is_market_hours=True,
                    is_fresh=True,
                    is_inline=True,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                )
            )
            current += timedelta(minutes=interval_minutes)
            idx += 1
        return data

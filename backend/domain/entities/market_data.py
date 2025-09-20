# =========================
# backend/domain/entities/market_data.py
# =========================
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class PriceSource(Enum):
    """Source of price data."""

    LAST_TRADE = "last_trade"
    MID_QUOTE = "mid_quote"
    BID = "bid"
    ASK = "ask"


@dataclass
class PriceData:
    """Market price data with metadata."""

    ticker: str
    price: float
    source: PriceSource
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    last_trade_price: Optional[float] = None
    last_trade_time: Optional[datetime] = None
    is_market_hours: bool = True
    is_fresh: bool = True  # Within 3 seconds
    is_inline: bool = True  # Within ±1% of mid-quote
    # OHLC data for daily bars
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None


@dataclass
class DailySummary:
    """Daily market data summary for a ticker."""

    ticker: str
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    vwap: float  # Volume Weighted Average Price
    volatility: float  # Daily volatility
    is_trading_day: bool = True


@dataclass
class MarketStatus:
    """Market status information."""

    is_open: bool
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    timezone: str = "US/Eastern"


@dataclass
class VolatilityData:
    """Volatility calculation data."""

    ticker: str
    timestamp: datetime
    volatility_1min: float
    volatility_5min: float
    volatility_1hour: float
    price_std_dev: float
    sample_size: int


@dataclass
class SimulationData:
    """Data structure for simulation and backtesting."""

    ticker: str
    start_date: datetime
    end_date: datetime
    price_data: List[PriceData]
    daily_summaries: List[DailySummary]
    volatility_data: List[VolatilityData]
    total_trading_days: int
    market_hours_data: List[PriceData]
    after_hours_data: List[PriceData]

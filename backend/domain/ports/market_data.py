# =========================
# backend/domain/ports/market_data.py
# =========================
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
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


@dataclass
class MarketStatus:
    """Market status information."""
    is_open: bool
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    timezone: str = "US/Eastern"


class MarketDataRepo(ABC):
    """Repository interface for market data."""
    
    @abstractmethod
    def get_price(self, ticker: str) -> Optional[PriceData]:
        """Get current price data for a ticker."""
        pass
    
    @abstractmethod
    def get_market_status(self) -> MarketStatus:
        """Get current market status."""
        pass
    
    @abstractmethod
    def validate_price(self, price_data: PriceData) -> Dict[str, Any]:
        """Validate price data for trading decisions."""
        pass
    
    @abstractmethod
    def get_reference_price(self, ticker: str) -> Optional[PriceData]:
        """Get reference price following the specification policy."""
        pass


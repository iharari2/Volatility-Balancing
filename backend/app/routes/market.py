# =========================
# backend/app/routes/market.py
# =========================

import logging
import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone

from app.di import container

router = APIRouter(prefix="/v1/market", tags=["market"])
logger = logging.getLogger(__name__)


@router.get("/status")
def get_market_status() -> Dict[str, Any]:
    """Get current market status."""
    try:
        market_data = container.market_data
        status = market_data.get_market_status()

        # Keep existing fields for backward compatibility, and add the
        # older "is_open" alias expected by some tests/clients.
        return {
            "is_market_open": status.is_open,
            "is_open": status.is_open,
            "is_after_hours": not status.is_open,
            "next_open": "09:30:00",  # Placeholder - would need actual market hours logic
            "next_close": "16:00:00",  # Placeholder - would need actual market hours logic
            "timezone": status.timezone,
            "current_time": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market status: {str(e)}")


@router.get("/state")
def get_market_state() -> Dict[str, Any]:
    """
    Get detailed market hours state for UI display.
    Returns: status (PRE_MARKET, OPEN, AFTER_HOURS, CLOSED), isOpen, timestamps
    """
    try:
        from datetime import datetime, timezone
        import pytz

        now = datetime.now(timezone.utc)
        est = pytz.timezone("US/Eastern")
        now_est = now.astimezone(est)
        hour = now_est.hour
        day = now_est.weekday()  # 0 = Monday, 6 = Sunday

        # Market is closed on weekends
        if day >= 5:  # Saturday (5) or Sunday (6)
            return {
                "status": "CLOSED",
                "isOpen": False,
                "currentTime": now.isoformat(),
            }

        # Pre-market: 4:00 AM - 9:30 AM EST
        if hour >= 4 and (hour < 9 or (hour == 9 and now_est.minute < 30)):
            return {
                "status": "PRE_MARKET",
                "isOpen": False,
                "currentTime": now.isoformat(),
            }

        # Market open: 9:30 AM - 4:00 PM EST
        if (hour == 9 and now_est.minute >= 30) or (hour >= 10 and hour < 16):
            return {
                "status": "OPEN",
                "isOpen": True,
                "currentTime": now.isoformat(),
            }

        # After-hours: 4:00 PM - 8:00 PM EST
        if hour >= 16 and hour < 20:
            return {
                "status": "AFTER_HOURS",
                "isOpen": False,
                "currentTime": now.isoformat(),
            }

        # Closed: 8:00 PM - 4:00 AM EST
        return {
            "status": "CLOSED",
            "isOpen": False,
            "currentTime": now.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market state: {str(e)}")


@router.post("/cache/clear")
def clear_market_cache(
    ticker: str = Query(None, description="Ticker to clear, or all if not specified"),
) -> Dict[str, Any]:
    """Clear market data cache for a ticker or all tickers."""
    try:
        market_data = container.market_data
        if hasattr(market_data, "clear_cache"):
            market_data.clear_cache(ticker)
            if ticker:
                return {"message": f"Cache cleared for {ticker}", "ticker": ticker}
            else:
                return {"message": "All market data cache cleared"}
        else:
            return {"message": "Cache clearing not available for this market data adapter"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.get("/price/{ticker}")
def get_market_price(
    ticker: str, force_refresh: bool = Query(False, description="Force refresh, bypass cache")
) -> Dict[str, Any]:
    """Get current market price for a ticker. Always fetches fresh data to avoid stale prices."""
    try:
        if os.getenv("MARKET_DATA_FORCE_ERROR", "false").lower() == "true":
            raise HTTPException(
                status_code=503, detail="Market data provider unavailable. Try again."
            )
        market_data = container.market_data
        if force_refresh and hasattr(market_data, "clear_cache"):
            market_data.clear_cache(ticker)
        price_data = market_data.get_price(ticker, force_refresh=force_refresh)

        if not price_data:
            error_kind = getattr(market_data, "last_error_kind", None)
            if os.getenv("MARKET_DATA_FALLBACK_MOCK", "false").lower() == "true":
                mock_price = 123.45
                now = datetime.now(timezone.utc)
                return {
                    "ticker": ticker,
                    "price": mock_price,
                    "source": "mock",
                    "timestamp": now.isoformat(),
                    "last_trade_time": None,
                    "is_market_hours": True,
                    "is_fresh": False,
                    "is_inline": True,
                    "validation": {
                        "valid": False,
                        "warnings": ["mock_price"],
                        "rejections": [],
                    },
                    "data_age_seconds": 0.0,
                    "open": mock_price,
                    "high": mock_price,
                    "low": mock_price,
                    "close": mock_price,
                }
            if error_kind == "provider_unavailable":
                logger.warning("Market data provider unavailable for %s", ticker)
                raise HTTPException(
                    status_code=503, detail="Market data provider unavailable. Try again."
                )
            logger.info("No market data found for %s", ticker)
            raise HTTPException(status_code=404, detail=f"No market data found for {ticker}")

        # Validate the price data
        validation = market_data.validate_price(price_data, allow_after_hours=True)

        # Include timestamp to show when data was fetched
        # Calculate data age
        data_age_seconds = (datetime.now(timezone.utc) - price_data.timestamp).total_seconds()

        # Log what we're returning
        print(f"📤 Returning price data for {ticker}:")
        print(f"   Price: ${price_data.price:.2f}")
        open_str = f"${price_data.open:.2f}" if price_data.open is not None else "N/A"
        high_str = f"${price_data.high:.2f}" if price_data.high is not None else "N/A"
        low_str = f"${price_data.low:.2f}" if price_data.low is not None else "N/A"
        close_str = f"${price_data.close:.2f}" if price_data.close is not None else "N/A"
        print(f"   OHLC - Open: {open_str}, High: {high_str}, Low: {low_str}, Close: {close_str}")
        print(f"   Source: {price_data.source.value}")
        print(f"   Timestamp: {price_data.timestamp.isoformat()}")
        print(f"   Data Age: {data_age_seconds:.1f} seconds ({data_age_seconds/3600:.2f} hours)")
        print(f"   Is Fresh: {price_data.is_fresh}")

        # Include OHLC data if available
        response_data = {
            "ticker": ticker,
            "price": price_data.price,
            "source": price_data.source.value,
            "timestamp": price_data.timestamp.isoformat(),
            "last_trade_time": (
                price_data.last_trade_time.isoformat() if price_data.last_trade_time else None
            ),
            "is_market_hours": price_data.is_market_hours,
            "is_fresh": price_data.is_fresh,
            "is_inline": price_data.is_inline,
            "validation": validation,
            "data_age_seconds": data_age_seconds,
        }

        # Add OHLC data if available
        if price_data.open is not None:
            response_data["open"] = price_data.open
        if price_data.high is not None:
            response_data["high"] = price_data.high
        if price_data.low is not None:
            response_data["low"] = price_data.low
        if price_data.close is not None:
            response_data["close"] = price_data.close

        return response_data
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error getting market price for %s", ticker)
        raise HTTPException(
            status_code=503, detail="Market data provider unavailable. Try again."
        )


@router.get("/historical/{ticker}")
def get_historical_data(
    ticker: str,
    start_date: str = Query(..., description="Start date in ISO format"),
    end_date: str = Query(..., description="End date in ISO format"),
    market_hours_only: bool = Query(False, description="Only include market hours data"),
) -> Dict[str, Any]:
    """Get historical price data for a ticker."""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        market_data = container.market_data
        historical_data = market_data.get_historical_data(ticker, start_dt, end_dt)

        if not historical_data:
            raise HTTPException(status_code=404, detail="ticker_not_found")

        # Convert to serializable format
        price_data = []
        for data_point in historical_data:
            price_data.append(
                {
                    "timestamp": data_point.timestamp.isoformat(),
                    "price": data_point.price,
                    "volume": getattr(data_point, "volume", None),
                    "is_market_hours": data_point.is_market_hours,
                }
            )

        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "market_hours_only": market_hours_only,
            "data_points": len(price_data),
            "price_data": price_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting historical data: {str(e)}")

# =========================
# backend/app/routes/market.py
# =========================

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone

from app.di import container

router = APIRouter(prefix="/v1/market", tags=["market"])


@router.get("/status")
def get_market_status() -> Dict[str, Any]:
    """Get current market status."""
    try:
        market_data = container.market_data
        status = market_data.get_market_status()

        return {
            "is_open": status.is_open,
            "timezone": status.timezone,
            "current_time": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market status: {str(e)}")


@router.get("/price/{ticker}")
def get_market_price(ticker: str) -> Dict[str, Any]:
    """Get current market price for a ticker."""
    try:
        market_data = container.market_data
        price_data = market_data.get_price(ticker)

        if not price_data:
            raise HTTPException(status_code=404, detail="ticker_not_found")

        return {
            "ticker": ticker,
            "price": price_data.price,
            "timestamp": price_data.timestamp.isoformat(),
            "source": price_data.source.value,
            "is_fresh": price_data.is_fresh,
            "is_inline": price_data.is_inline,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market price: {str(e)}")


@router.get("/historical/{ticker}")
def get_historical_data(
    ticker: str,
    start_date: str = Query(..., description="Start date in ISO format"),
    end_date: str = Query(..., description="End date in ISO format"),
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
                    "source": data_point.source.value,
                    "is_fresh": data_point.is_fresh,
                    "is_inline": data_point.is_inline,
                }
            )

        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "price_data": price_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting historical data: {str(e)}")

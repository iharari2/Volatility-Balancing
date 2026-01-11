#!/usr/bin/env python3
"""Test script to check what market data YFinance is actually returning"""

import os
import yfinance as yf
from datetime import datetime, timezone
import pytz
import pytest
from typing import Optional

pytestmark = pytest.mark.online


def _truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() not in ("0", "false", "no", "off", "")


if _truthy(os.getenv("TICK_DETERMINISTIC")):
    pytest.skip("Skipping live yfinance test in deterministic mode.", allow_module_level=True)


def test_yfinance_data(ticker="AAPL"):
    """Test what data YFinance returns"""
    print(f"\n{'='*60}")
    print(f"Testing YFinance data for {ticker}")
    print(f"{'='*60}\n")

    stock = yf.Ticker(ticker)
    current_time = datetime.now(timezone.utc)
    eastern = pytz.timezone("US/Eastern")
    current_time_et = current_time.astimezone(eastern)

    print(f"Current time (UTC): {current_time}")
    print(f"Current time (ET):  {current_time_et}\n")

    # Test 1: fast_info
    print("1. Testing fast_info:")
    try:
        fast_info = stock.fast_info
        print(f"   fast_info type: {type(fast_info)}")
        print(f"   fast_info keys: {list(fast_info.keys())[:10]}...")

        last_price = fast_info.get("lastPrice")
        regular_price = fast_info.get("regularMarketPrice")
        previous_close = fast_info.get("previousClose")

        print(f"   lastPrice: {last_price}")
        print(f"   regularMarketPrice: {regular_price}")
        print(f"   previousClose: {previous_close}")
        print(f"   bid: {fast_info.get('bid')}")
        print(f"   ask: {fast_info.get('ask')}")
        print(f"   volume: {fast_info.get('regularMarketVolume')}")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback

        traceback.print_exc()

    print()

    # Test 2: info
    print("2. Testing info:")
    try:
        info = stock.info
        print(f"   currentPrice: {info.get('currentPrice')}")
        print(f"   regularMarketPrice: {info.get('regularMarketPrice')}")
        print(f"   regularMarketPreviousClose: {info.get('regularMarketPreviousClose')}")
        print(f"   bid: {info.get('bid')}")
        print(f"   ask: {info.get('ask')}")
        print(f"   volume: {info.get('volume')}")
        print(f"   quoteType: {info.get('quoteType')}")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback

        traceback.print_exc()

    print()

    # Test 3: history (1 day, 1 minute)
    print("3. Testing history (1d, 1m):")
    try:
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            latest = hist.iloc[-1]
            latest_time = latest.name
            if latest_time.tzinfo is None:
                latest_time = latest_time.replace(tzinfo=eastern).astimezone(timezone.utc)
            else:
                latest_time = latest_time.astimezone(timezone.utc)

            age_seconds = (current_time - latest_time).total_seconds()
            age_minutes = age_seconds / 60
            age_hours = age_minutes / 60
            age_days = age_hours / 24

            print(f"   Latest timestamp: {latest_time}")
            print(
                f"   Age: {age_seconds:.0f} seconds ({age_minutes:.1f} minutes, {age_hours:.1f} hours, {age_days:.1f} days)"
            )
            print(f"   Close: ${latest['Close']:.2f}")
            print(f"   High: ${latest['High']:.2f}")
            print(f"   Low: ${latest['Low']:.2f}")
            print(f"   Volume: {int(latest['Volume'])}")
            print(f"   Total data points: {len(hist)}")
        else:
            print("   ERROR: History is empty!")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback

        traceback.print_exc()

    print()

    # Test 4: Try to get the most current data
    print("4. Best current price:")
    try:
        # Try multiple methods
        best_price = None
        best_source = None

        # Method 1: fast_info
        try:
            fast_info = stock.fast_info
            price = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice")
            if price and price > 0:
                best_price = price
                best_source = "fast_info"
        except:
            pass

        # Method 2: info
        if not best_price:
            try:
                info = stock.info
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                if price and price > 0:
                    best_price = price
                    best_source = "info"
            except:
                pass

        # Method 3: history latest
        if not best_price:
            try:
                hist = stock.history(period="1d", interval="1m")
                if not hist.empty:
                    best_price = hist.iloc[-1]["Close"]
                    best_source = "history (latest)"
            except:
                pass

        if best_price:
            print(f"   ✅ Best price: ${best_price:.2f} (from {best_source})")
        else:
            print("   ❌ Could not get any price!")

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback

        traceback.print_exc()

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    import sys

    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    test_yfinance_data(ticker)

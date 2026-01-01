#!/usr/bin/env python3
"""Test Step 2: Market Data Fetching"""

import sys
from pathlib import Path
from decimal import Decimal

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.di import container


def test_market_data(ticker: str) -> bool:
    """
    Test fetching market data for a ticker.

    Returns:
        True if market data fetched successfully, False otherwise
    """
    print("=" * 80)
    print("Testing Step 2: Market Data Fetching")
    print("=" * 80)
    print(f"Fetching market data for: {ticker}")
    print()

    try:
        # Fetch price data - YFinanceAdapter uses get_reference_price
        price_data = container.market_data.get_reference_price(ticker)

        if not price_data:
            print(f"❌ No market data available for {ticker}")
            return False

        print("✅ Market Data Results:")
        print(f"   Ticker: {ticker}")
        print(f"   Price: ${price_data.price}")
        print(f"   Price Type: {type(price_data.price).__name__}")
        print(f"   Timestamp: {price_data.timestamp}")
        print(
            f"   Source: {price_data.source.value if hasattr(price_data.source, 'value') else price_data.source}"
        )
        print(f"   Is Market Hours: {price_data.is_market_hours}")
        print(f"   Is Fresh: {price_data.is_fresh}")

        # Verify price is Decimal or can be converted
        if isinstance(price_data.price, Decimal):
            price_float = float(price_data.price)
            print(f"   Price as float: ${price_float:.2f}")
        elif isinstance(price_data.price, (int, float)):
            price_decimal = Decimal(str(price_data.price))
            print(f"   Price as Decimal: ${price_decimal}")
        else:
            print(f"   ⚠️  WARNING: Price type {type(price_data.price)} may cause type errors")

        # Test conversion
        try:
            test_calc = float(price_data.price) * 10
            print(f"   ✅ Type conversion test passed: ${test_calc:.2f}")
        except (TypeError, ValueError) as e:
            print(f"   ❌ Type conversion test failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Error fetching market data: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_step2_market_data.py <ticker>")
        print("Example: python test_step2_market_data.py AAPL")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    success = test_market_data(ticker)
    sys.exit(0 if success else 1)

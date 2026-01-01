#!/usr/bin/env python3
"""Test script to verify OHLC data is fresh"""

import sys

sys.path.insert(0, ".")

from app.di import container

# Clear all cache
container.market_data.clear_cache()

# Test INTC
print("Testing INTC OHLC data...")
price_data = container.market_data.get_price("INTC", force_refresh=True)

if price_data:
    print("\n✅ INTC OHLC Data:")
    print(f"   Open:  ${price_data.open:.2f}" if price_data.open else "   Open:  N/A")
    print(f"   High:  ${price_data.high:.2f}" if price_data.high else "   High:  N/A")
    print(f"   Low:   ${price_data.low:.2f}" if price_data.low else "   Low:   N/A")
    print(f"   Close: ${price_data.close:.2f}" if price_data.close else "   Close: N/A")
    print(f"   Price: ${price_data.price:.2f}")
    print(f"   Timestamp: {price_data.timestamp}")

    # Verify it's current (should be today's open, not old)
    if price_data.open:
        if price_data.open < 40.0 or price_data.open > 41.0:
            print(
                f"\n⚠️  WARNING: Open price ${price_data.open:.2f} seems stale (should be ~$40.74)"
            )
        else:
            print(f"\n✅ Open price looks current: ${price_data.open:.2f}")
else:
    print("❌ No price data returned")

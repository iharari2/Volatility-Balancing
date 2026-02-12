#!/usr/bin/env python3
"""
Debug script to test market data storage and retrieval directly.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infrastructure.market.yfinance_adapter import YFinanceAdapter
from infrastructure.market.market_data_storage import MarketDataStorage


def test_market_data_storage():
    """Test the market data storage and retrieval pipeline."""
    print("=== Testing Market Data Storage Pipeline ===")

    # Create adapters
    yfinance_adapter = YFinanceAdapter()
    market_storage = MarketDataStorage()

    # Test with recent dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)

    print(f"Fetching data for AAPL from {start_date} to {end_date}")

    # Fetch data from yfinance
    try:
        historical_data = yfinance_adapter.fetch_historical_data(
            ticker="AAPL", start_date=start_date, end_date=end_date
        )
        print(f"✅ yfinance returned {len(historical_data)} data points")

        if historical_data:
            first = historical_data[0]
            last = historical_data[-1]
            print(
                f"First data: price={first.price}, volume={first.volume}, timestamp={first.timestamp}"
            )
            print(
                f"Last data: price={last.price}, volume={last.volume}, timestamp={last.timestamp}"
            )
    except Exception as e:
        print(f"❌ yfinance error: {e}")
        return

    # Store data in market storage
    print(f"\nStoring {len(historical_data)} data points in market storage...")
    for price_data in historical_data:
        market_storage.store_price_data("AAPL", price_data)

    print("✅ Stored data in market storage")

    # Test retrieval
    print("\nTesting data retrieval...")

    # Test get_historical_data
    retrieved_data = market_storage.get_historical_data("AAPL", start_date, end_date)
    print(f"✅ Retrieved {len(retrieved_data)} data points from get_historical_data")

    if retrieved_data:
        first = retrieved_data[0]
        last = retrieved_data[-1]
        print(
            f"First retrieved: price={first.price}, volume={first.volume}, timestamp={first.timestamp}"
        )
        print(
            f"Last retrieved: price={last.price}, volume={last.volume}, timestamp={last.timestamp}"
        )

    # Test get_simulation_data
    print("\nTesting get_simulation_data...")
    sim_data = market_storage.get_simulation_data(
        "AAPL", start_date, end_date, include_after_hours=True
    )
    print(f"✅ get_simulation_data returned {len(sim_data.price_data)} data points")

    if sim_data.price_data:
        first = sim_data.price_data[0]
        last = sim_data.price_data[-1]
        print(
            f"First sim data: price={first.price}, volume={first.volume}, timestamp={first.timestamp}"
        )
        print(
            f"Last sim data: price={last.price}, volume={last.volume}, timestamp={last.timestamp}"
        )
    else:
        print("❌ No data in sim_data.price_data!")

    # Check what's in the storage
    print("\nChecking storage contents...")
    print(f"price_history keys: {list(market_storage.price_history.keys())}")
    if "AAPL" in market_storage.price_history:
        stored_count = len(market_storage.price_history["AAPL"])
        print(f"Stored AAPL data points: {stored_count}")
        if stored_count > 0:
            first_stored = market_storage.price_history["AAPL"][0]
            print(
                f"First stored: price={first_stored.price}, volume={first_stored.volume}, timestamp={first_stored.timestamp}"
            )


if __name__ == "__main__":
    test_market_data_storage()

#!/usr/bin/env python3
"""
Debug script to inspect price_data objects in simulation.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infrastructure.market.yfinance_adapter import YFinanceAdapter
from infrastructure.market.market_data_storage import MarketDataStorage
from application.use_cases.simulation_unified_uc import SimulationUnifiedUC
from infrastructure.persistence.memory.positions_repo_mem import InMemoryPositionsRepo
from infrastructure.persistence.memory.events_repo_mem import InMemoryEventsRepo
from infrastructure.time.clock import Clock


def debug_price_data_objects():
    """Debug the price_data objects in simulation."""
    print("=== Debugging Price Data Objects in Simulation ===")

    # Create adapters
    yfinance_adapter = YFinanceAdapter()
    market_storage = MarketDataStorage()

    # Test with past dates to avoid future date error
    end_date = datetime.now() - timedelta(days=1)
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
            print(
                f"First yfinance data: price={first.price}, volume={first.volume}, type={type(first).__name__}"
            )
            print(
                f"First data attributes: {[attr for attr in dir(first) if not attr.startswith('_')]}"
            )
    except Exception as e:
        print(f"❌ yfinance error: {e}")
        return

    # Store data in market storage
    print(f"\nStoring {len(historical_data)} data points in market storage...")
    for price_data in historical_data:
        market_storage.store_price_data("AAPL", price_data)

    # Get simulation data
    sim_data = market_storage.get_simulation_data(
        "AAPL", start_date, end_date, include_after_hours=True
    )
    print(f"✅ get_simulation_data returned {len(sim_data.price_data)} data points")

    if sim_data.price_data:
        first_sim = sim_data.price_data[0]
        print(
            f"First sim data: price={first_sim.price}, volume={first_sim.volume}, type={type(first_sim).__name__}"
        )
        print(
            f"First sim attributes: {[attr for attr in dir(first_sim) if not attr.startswith('_')]}"
        )

        # Check if volume is accessible
        print(f"Has volume attr: {hasattr(first_sim, 'volume')}")
        print(f"Volume value: {getattr(first_sim, 'volume', 'NO_VOLUME_ATTR')}")

        # Check the actual object
        print(f"Object dict: {first_sim.__dict__ if hasattr(first_sim, '__dict__') else 'NO_DICT'}")

    # Now test the simulation use case
    print("\n=== Testing Simulation Use Case ===")

    # Create simulation use case
    sim_uc = SimulationUnifiedUC(
        market_data=yfinance_adapter,
        positions=InMemoryPositionsRepo(),
        events=InMemoryEventsRepo(),
        clock=Clock(),
    )

    # Run a simple simulation to see what price_data objects look like
    try:
        result = sim_uc.run_simulation(
            ticker="AAPL",
            start_date=start_date,
            end_date=end_date,
            initial_cash=10000,
            position_config={
                "trigger_threshold_pct": 0.01,
                "rebalance_ratio": 0.5,
                "commission_rate": 0.001,
                "min_notional": 100,
                "allow_after_hours": True,
                "guardrails": {
                    "min_stock_alloc_pct": 0.25,
                    "max_stock_alloc_pct": 0.75,
                    "max_orders_per_day": 10,
                },
            },
            include_after_hours=True,
        )

        print("✅ Simulation completed successfully")
        print(f"Algorithm trades: {result.algorithm_trades}")

        # Check trigger analysis
        triggers = result.trigger_analysis
        print(f"Total triggers: {len(triggers)}")

        if triggers:
            first_trigger = triggers[0]
            print(
                f"First trigger: price={first_trigger.get('price')}, volume={first_trigger.get('volume')}"
            )

            # Check debug info if available
            debug_info = getattr(result, "debug_info", [])
            print(f"Debug info entries: {len(debug_info)}")
            if debug_info:
                first_debug = debug_info[0]
                print(f"First debug: {first_debug}")

    except Exception as e:
        print(f"❌ Simulation error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_price_data_objects()

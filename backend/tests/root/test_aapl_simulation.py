#!/usr/bin/env python3
"""
Test script for running a complete 1-year AAPL simulation.

This script demonstrates how to run a full simulation without needing a position.
"""

import requests
from datetime import datetime, timedelta, timezone
import json

# Configuration
BASE_URL = "http://localhost:8000"
TICKER = "AAPL"

# Calculate 1 year ago from today
end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=365)

# Format dates for API
start_date_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
end_date_str = end_date.strftime("%Y-%m-%dT23:59:59Z")

print("=" * 80)
print("AAPL 1-Year Simulation Test")
print("=" * 80)
print(f"Ticker: {TICKER}")
print(f"Start Date: {start_date_str}")
print(f"End Date: {end_date_str}")
print("Duration: 365 days")
print("=" * 80)
print()

# Prepare simulation request
simulation_request = {
    "ticker": TICKER,
    "start_date": start_date_str,
    "end_date": end_date_str,
    "initial_cash": 10000.0,
    "include_after_hours": False,
    "intraday_interval_minutes": 30,  # 30-minute intervals for intraday data
    "position_config": {
        "trigger_threshold_pct": 0.03,  # 3% trigger threshold
        "rebalance_ratio": 1.6667,  # Rebalance ratio
        "commission_rate": 0.0001,  # 0.01% commission
        "min_notional": 100.0,  # Minimum $100 per trade
        "allow_after_hours": False,
        "guardrails": {
            "min_stock_alloc_pct": 0.25,  # Minimum 25% in stock
            "max_stock_alloc_pct": 0.75,  # Maximum 75% in stock
        },
    },
}

print("Sending simulation request...")
print(f"Endpoint: {BASE_URL}/v1/simulation/run")
print()

try:
    # Make the request
    response = requests.post(
        f"{BASE_URL}/v1/simulation/run",
        json=simulation_request,
        timeout=600,  # 10 minute timeout for long simulations
    )

    print(f"Response Status: {response.status_code}")
    print()

    if response.status_code == 200:
        result = response.json()

        print("=" * 80)
        print("SIMULATION RESULTS")
        print("=" * 80)
        print(f"Simulation ID: {result.get('simulation_id', 'N/A')}")
        print(f"Ticker: {result.get('ticker', 'N/A')}")
        print(f"Start Date: {result.get('start_date', 'N/A')}")
        print(f"End Date: {result.get('end_date', 'N/A')}")
        print(f"Total Trading Days: {result.get('total_trading_days', 'N/A')}")
        print()
        print("PERFORMANCE METRICS")
        print("-" * 80)
        print(f"Initial Cash: ${result.get('initial_cash', 0):,.2f}")
        print()
        print("Algorithm Performance:")
        print(f"  Return: {result.get('algorithm_return_pct', 0):.2f}%")
        print(f"  P&L: ${result.get('algorithm_pnl', 0):,.2f}")
        print(f"  Total Trades: {result.get('algorithm_trades', 0)}")
        print(f"  Sharpe Ratio: {result.get('sharpe_ratio', 0):.2f}")
        print(f"  Max Drawdown: {result.get('max_drawdown', 0):.2f}%")
        print(f"  Volatility: {result.get('volatility', 0):.2f}%")
        print()
        print("Buy & Hold Performance:")
        print(f"  Return: {result.get('buy_hold_return_pct', 0):.2f}%")
        print(f"  P&L: ${result.get('buy_hold_pnl', 0):,.2f}")
        print()
        print("Comparison:")
        print(f"  Excess Return: {result.get('excess_return', 0):.2f}%")
        print("=" * 80)
        print()
        print("✅ Simulation completed successfully!")
        print()
        print("Full JSON Response:")
        print(json.dumps(result, indent=2))

    else:
        print("❌ Simulation failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.ConnectionError:
    print("❌ Error: Could not connect to the backend server.")
    print(f"Make sure the backend is running at {BASE_URL}")
    print()
    print("Start the backend with:")
    print("  cd backend")
    print("  python -m uvicorn app.main:app --reload")

except requests.exceptions.Timeout:
    print("❌ Error: Simulation timed out (took longer than 10 minutes)")
    print("This might be normal for a 1-year simulation with intraday data.")
    print("Try reducing the date range or increasing the intraday_interval_minutes.")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback

    traceback.print_exc()

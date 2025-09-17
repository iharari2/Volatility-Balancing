#!/usr/bin/env python3
"""
Phase 3 Demo: Market Data Integration with After-Hours Trading
=============================================================

This script demonstrates the complete Phase 3 implementation:
- Real-time market data integration with yfinance
- After-hours trading configuration
- Price validation and reference price logic
- Market status and hours management
- Enhanced evaluation with market data

Run this after starting the server:
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000/v1"


def print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_result(title: str, result: Dict[str, Any]) -> None:
    print(f"\n{title}:")
    print(json.dumps(result, indent=2, default=str))


def test_market_status() -> None:
    """Test market status endpoint."""
    print_section("Testing Market Status")

    response = requests.get(f"{BASE_URL}/market/status")
    if response.status_code == 200:
        result = response.json()
        print_result("Market Status", result)
    else:
        print(f"Error getting market status: {response.status_code} - {response.text}")


def test_market_price(ticker: str) -> Dict[str, Any]:
    """Test market price endpoint."""
    print_section(f"Testing Market Price for {ticker}")

    response = requests.get(f"{BASE_URL}/market/price/{ticker}")
    if response.status_code == 200:
        result = response.json()
        print_result(f"Market Price for {ticker}", result)
        return result
    else:
        print(f"Error getting market price: {response.status_code} - {response.text}")
        return {}


def create_position_with_after_hours(allow_after_hours: bool = False) -> str:
    """Create a test position with after-hours configuration."""
    print_section(f"Creating Position (After-Hours: {allow_after_hours})")

    position_data = {
        "ticker": "AAPL",
        "qty": 100.0,
        "cash": 10000.0,
        "order_policy": {
            "trigger_threshold_pct": 0.03,  # 3%
            "rebalance_ratio": 1.6667,
            "commission_rate": 0.0001,  # 0.01%
            "min_notional": 100.0,
            "allow_after_hours": allow_after_hours,
        },
        "guardrails": {
            "min_stock_alloc_pct": 0.25,  # 25%
            "max_stock_alloc_pct": 0.75,  # 75%
            "max_orders_per_day": 5,
        },
    }

    response = requests.post(f"{BASE_URL}/positions", json=position_data)
    if response.status_code == 201:
        result = response.json()
        print_result("Position Created", result)
        return result["id"]
    else:
        print(f"Error creating position: {response.status_code} - {response.text}")
        return None


def test_evaluation_with_market_data(position_id: str) -> None:
    """Test evaluation using real market data."""
    print_section("Testing Evaluation with Market Data")

    response = requests.post(f"{BASE_URL}/positions/{position_id}/evaluate/market")
    if response.status_code == 200:
        result = response.json()
        print_result("Market Data Evaluation", result)

        if result.get("market_data"):
            market_data = result["market_data"]
            print(f"\nMarket Data Details:")
            print(f"  Price: ${market_data['price']:.2f}")
            print(f"  Source: {market_data['source']}")
            print(f"  Market Hours: {market_data['is_market_hours']}")
            print(f"  Fresh: {market_data['is_fresh']}")
            print(f"  Inline: {market_data['is_inline']}")
            if market_data.get("validation"):
                validation = market_data["validation"]
                print(f"  Valid: {validation['valid']}")
                if validation.get("warnings"):
                    print(f"  Warnings: {', '.join(validation['warnings'])}")
                if validation.get("rejections"):
                    print(f"  Rejections: {', '.join(validation['rejections'])}")
    else:
        print(f"Error evaluating with market data: {response.status_code} - {response.text}")


def test_auto_sized_order_with_market_data(position_id: str) -> None:
    """Test auto-sized order with market data."""
    print_section("Testing Auto-Sized Order with Market Data")

    response = requests.post(f"{BASE_URL}/positions/{position_id}/orders/auto-size/market")
    if response.status_code == 200:
        result = response.json()
        print_result("Auto-Sized Order with Market Data", result)

        if result.get("market_data"):
            market_data = result["market_data"]
            print(f"\nMarket Data in Order:")
            print(f"  Price: ${market_data['price']:.2f}")
            print(f"  Source: {market_data['source']}")
            print(f"  Market Hours: {market_data['is_market_hours']}")
    else:
        print(f"Error submitting auto-sized order: {response.status_code} - {response.text}")


def test_after_hours_scenarios() -> None:
    """Test after-hours trading scenarios."""
    print_section("Testing After-Hours Trading Scenarios")

    # Test 1: Position with after-hours disabled
    print("\n--- Scenario 1: After-Hours Disabled ---")
    pos_id_disabled = create_position_with_after_hours(allow_after_hours=False)
    if pos_id_disabled:
        # Set anchor price
        requests.post(f"{BASE_URL}/positions/{pos_id_disabled}/anchor", params={"price": 150.0})
        test_evaluation_with_market_data(pos_id_disabled)

    # Test 2: Position with after-hours enabled
    print("\n--- Scenario 2: After-Hours Enabled ---")
    pos_id_enabled = create_position_with_after_hours(allow_after_hours=True)
    if pos_id_enabled:
        # Set anchor price
        requests.post(f"{BASE_URL}/positions/{pos_id_enabled}/anchor", params={"price": 150.0})
        test_evaluation_with_market_data(pos_id_enabled)


def test_price_validation() -> None:
    """Test price validation logic."""
    print_section("Testing Price Validation")

    # Test with a real ticker
    ticker = "AAPL"
    price_data = test_market_price(ticker)

    if price_data:
        print(f"\nPrice Validation Analysis:")
        print(f"  Ticker: {price_data['ticker']}")
        print(f"  Price: ${price_data['price']:.2f}")
        print(f"  Source: {price_data['source']}")
        print(f"  Market Hours: {price_data['is_market_hours']}")
        print(f"  Fresh: {price_data['is_fresh']}")
        print(f"  Inline: {price_data['is_inline']}")

        # Test with different tickers
        test_tickers = ["MSFT", "GOOGL", "TSLA"]
        for test_ticker in test_tickers:
            print(f"\nTesting {test_ticker}:")
            test_market_price(test_ticker)


def main():
    """Run the Phase 3 demo."""
    print("Phase 3 Demo: Market Data Integration with After-Hours Trading")
    print("=" * 70)

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/healthz")
        if response.status_code != 200:
            print("Error: Server not running. Please start with:")
            print("python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
            return
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to server. Please start with:")
        print("python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return

    # Test market status
    test_market_status()

    # Test price validation
    test_price_validation()

    # Test after-hours scenarios
    test_after_hours_scenarios()

    print_section("Demo Complete")
    print("Phase 3 implementation includes:")
    print("✅ Real-time market data integration")
    print("✅ After-hours trading configuration")
    print("✅ Price validation and reference price logic")
    print("✅ Market status and hours management")
    print("✅ Enhanced evaluation with market data")
    print("\nNext steps: Dividend handling and UX improvements")


if __name__ == "__main__":
    main()



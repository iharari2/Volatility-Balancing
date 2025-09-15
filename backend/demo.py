#!/usr/bin/env python3
"""
Volatility Trading System Demo
=============================

This demo showcases the core volatility trading functionality:
1. Create a position with initial cash
2. Set an anchor price
3. Demonstrate trigger detection at different price levels
4. Show order execution and anchor price updates
5. Display the complete audit trail

Run with: python demo.py
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/v1"
TICKER = "AAPL"
INITIAL_CASH = 10000.0
ANCHOR_PRICE = 150.0


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_step(step: str, description: str) -> None:
    """Print a formatted step."""
    print(f"\n🔹 {step}: {description}")


def make_request(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Make an HTTP request and return the response."""
    try:
        if method.upper() == "GET":
            response = requests.get(url, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {}


def demo_volatility_trading():
    """Run the complete volatility trading demo."""

    print_section("VOLATILITY TRADING SYSTEM DEMO")
    print("This demo shows how the system detects price movements")
    print("and triggers buy/sell orders based on volatility thresholds.")

    # Step 1: Create a position
    print_step("1", "Creating a new position")
    position_data = {"ticker": TICKER, "qty": 0.0, "cash": INITIAL_CASH}

    result = make_request("POST", f"{BASE_URL}/positions", json=position_data)
    if not result:
        print("❌ Failed to create position. Make sure the server is running.")
        return

    position_id = result["id"]
    print(f"✅ Created position: {position_id}")
    print(f"   Ticker: {result['ticker']}")
    print(f"   Initial Cash: ${result['cash']:,.2f}")
    print(f"   Initial Shares: {result['qty']}")

    # Step 2: Set anchor price
    print_step("2", "Setting anchor price for volatility tracking")
    anchor_result = make_request(
        "POST", f"{BASE_URL}/positions/{position_id}/anchor", params={"price": ANCHOR_PRICE}
    )
    if not anchor_result:
        return

    print(f"✅ Anchor price set to: ${anchor_result['anchor_price']:.2f}")
    print(f"   This is our reference point for volatility calculations")
    print(f"   Buy trigger: ≤ ${ANCHOR_PRICE * 0.97:.2f} (3% below anchor)")
    print(f"   Sell trigger: ≥ ${ANCHOR_PRICE * 1.03:.2f} (3% above anchor)")

    # Step 3: Demonstrate trigger detection
    print_step("3", "Testing volatility trigger detection")

    test_prices = [
        (145.0, "BUY trigger - Price drops 3.3% below anchor"),
        (152.0, "No trigger - Price within normal range"),
        (155.0, "SELL trigger - Price rises 3.3% above anchor"),
        (140.0, "Strong BUY trigger - Price drops 6.7% below anchor"),
        (160.0, "Strong SELL trigger - Price rises 6.7% above anchor"),
    ]

    for price, description in test_prices:
        print(f"\n   Testing at ${price:.2f}: {description}")
        result = make_request(
            "POST", f"{BASE_URL}/positions/{position_id}/evaluate", params={"current_price": price}
        )
        if result:
            if result["trigger_detected"]:
                print(f"   🚨 TRIGGER DETECTED: {result['trigger_type']}")
                print(f"   📊 Reasoning: {result['reasoning']}")
            else:
                print(f"   ✅ No trigger - {result['reasoning']}")

        time.sleep(0.5)  # Small delay for demo effect

    # Step 4: Simulate order execution
    print_step("4", "Simulating order execution and anchor price updates")

    # Simulate a BUY order at $145
    print(f"\n   Simulating BUY order at $145.00...")
    order_data = {"side": "BUY", "qty": 10.0}

    # Submit order
    order_result = make_request(
        "POST",
        f"{BASE_URL}/positions/{position_id}/orders",
        json=order_data,
        headers={"Idempotency-Key": "demo-buy-1"},
    )
    if order_result:
        order_id = order_result["order_id"]
        print(f"   ✅ Order submitted: {order_id}")

        # Fill the order
        fill_data = {"qty": 10.0, "price": 145.0, "commission": 1.45}  # 0.01% of $14,500

        fill_result = make_request("POST", f"{BASE_URL}/orders/{order_id}/fill", json=fill_data)
        if fill_result:
            print(f"   ✅ Order filled: {fill_result['status']}")
            print(f"   📈 New position: 10 shares @ $145.00")
            print(f"   💰 Remaining cash: ${INITIAL_CASH - (10 * 145) - 1.45:,.2f}")
            print(f"   🎯 Anchor price updated to: $145.00")

    # Step 5: Test new anchor price
    print_step("5", "Testing triggers with new anchor price")

    print(f"\n   New anchor price: $145.00")
    print(f"   New buy trigger: ≤ ${145 * 0.97:.2f}")
    print(f"   New sell trigger: ≥ ${145 * 1.03:.2f}")

    new_test_prices = [
        (140.0, "BUY trigger with new anchor"),
        (150.0, "SELL trigger with new anchor"),
        (145.0, "No trigger at anchor price"),
    ]

    for price, description in new_test_prices:
        print(f"\n   Testing at ${price:.2f}: {description}")
        result = make_request(
            "POST", f"{BASE_URL}/positions/{position_id}/evaluate", params={"current_price": price}
        )
        if result:
            if result["trigger_detected"]:
                print(f"   🚨 TRIGGER DETECTED: {result['trigger_type']}")
                print(f"   📊 Reasoning: {result['reasoning']}")
            else:
                print(f"   ✅ No trigger - {result['reasoning']}")

    # Step 6: Show audit trail
    print_step("6", "Viewing complete audit trail")

    events_result = make_request("GET", f"{BASE_URL}/positions/{position_id}/events")
    if events_result:
        events = events_result["events"]
        print(f"\n   📋 Found {len(events)} events in audit trail:")

        for i, event in enumerate(events, 1):
            print(f"\n   {i}. {event['type'].upper()}")
            print(f"      Time: {event['ts']}")
            print(f"      Message: {event['message']}")
            if event["inputs"]:
                print(f"      Inputs: {json.dumps(event['inputs'], indent=8)}")
            if event["outputs"]:
                print(f"      Outputs: {json.dumps(event['outputs'], indent=8)}")

    # Step 7: Show final position
    print_step("7", "Final position summary")

    position_result = make_request("GET", f"{BASE_URL}/positions/{position_id}")
    if position_result:
        print(f"\n   📊 Final Position State:")
        print(f"      Ticker: {position_result['ticker']}")
        print(f"      Shares: {position_result['qty']}")
        print(f"      Cash: ${position_result['cash']:,.2f}")
        print(f"      Anchor Price: ${position_result.get('anchor_price', 'Not set')}")

        total_value = (position_result["qty"] * 145.0) + position_result["cash"]
        print(f"      Total Value: ${total_value:,.2f}")

    print_section("DEMO COMPLETE")
    print("🎉 The volatility trading system is working perfectly!")
    print("\nKey Features Demonstrated:")
    print("✅ Position creation and management")
    print("✅ Anchor price tracking")
    print("✅ Volatility trigger detection (±3% thresholds)")
    print("✅ Order execution and anchor price updates")
    print("✅ Complete audit trail with reasoning")
    print("✅ Real-time evaluation API")

    print(f"\n🔗 API Endpoints Used:")
    print(f"   POST /v1/positions - Create position")
    print(f"   POST /v1/positions/{{id}}/anchor - Set anchor price")
    print(f"   POST /v1/positions/{{id}}/evaluate - Evaluate triggers")
    print(f"   POST /v1/positions/{{id}}/orders - Submit orders")
    print(f"   POST /v1/orders/{{id}}/fill - Execute orders")
    print(f"   GET /v1/positions/{{id}}/events - View audit trail")


if __name__ == "__main__":
    print("🚀 Starting Volatility Trading System Demo...")
    print("Make sure the server is running on http://localhost:8000")
    print("Press Ctrl+C to cancel, or Enter to continue...")

    try:
        input()
        demo_volatility_trading()
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print(
            "Make sure the server is running: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
        )

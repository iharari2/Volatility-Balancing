#!/usr/bin/env python3
"""
Phase 2 Demo: Advanced Order Sizing & Guardrails
================================================

This script demonstrates the complete Phase 2 implementation:
- Order sizing formula: ΔQ_raw = (P_anchor / P) × r × ((A + C) / P)
- Guardrail trimming to enforce Asset% ∈ [25%, 75%]
- Auto-rebalancing when position drifts outside bounds
- Enhanced order validation
- Auto-sized order submission

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


def create_position() -> str:
    """Create a test position with guardrails."""
    print_section("Creating Test Position")

    position_data = {
        "ticker": "AAPL",
        "qty": 100.0,
        "cash": 10000.0,
        "guardrails": {
            "min_stock_alloc_pct": 0.25,  # 25%
            "max_stock_alloc_pct": 0.75,  # 75%
            "max_orders_per_day": 5,
        },
        "order_policy": {
            "trigger_threshold_pct": 0.03,  # 3%
            "rebalance_ratio": 1.6667,
            "commission_rate": 0.0001,  # 0.01%
            "min_notional": 100.0,
        },
    }

    response = requests.post(f"{BASE_URL}/positions", json=position_data)
    if response.status_code == 201:
        result = response.json()
        print_result("Position Created", result)
        return result["position_id"]
    else:
        print(f"Error creating position: {response.status_code} - {response.text}")
        return None


def set_anchor_price(position_id: str, price: float) -> None:
    """Set the anchor price for volatility trading."""
    print_section(f"Setting Anchor Price to ${price:.2f}")

    response = requests.post(f"{BASE_URL}/positions/{position_id}/anchor", params={"price": price})
    if response.status_code == 200:
        result = response.json()
        print_result("Anchor Price Set", result)
    else:
        print(f"Error setting anchor price: {response.status_code} - {response.text}")


def test_trigger_detection(position_id: str, current_price: float) -> Dict[str, Any]:
    """Test trigger detection and order sizing."""
    print_section(f"Testing Trigger Detection at ${current_price:.2f}")

    response = requests.post(
        f"{BASE_URL}/positions/{position_id}/evaluate", params={"current_price": current_price}
    )
    if response.status_code == 200:
        result = response.json()
        print_result("Evaluation Result", result)
        return result
    else:
        print(f"Error evaluating position: {response.status_code} - {response.text}")
        return {}


def test_auto_sized_order(position_id: str, current_price: float) -> Dict[str, Any]:
    """Test auto-sized order submission."""
    print_section(f"Testing Auto-Sized Order at ${current_price:.2f}")

    response = requests.post(
        f"{BASE_URL}/positions/{position_id}/orders/auto-size",
        params={"current_price": current_price},
    )
    if response.status_code == 200:
        result = response.json()
        print_result("Auto-Sized Order Result", result)
        return result
    else:
        print(f"Error submitting auto-sized order: {response.status_code} - {response.text}")
        return {}


def test_guardrail_scenarios(position_id: str) -> None:
    """Test various guardrail scenarios."""
    print_section("Testing Guardrail Scenarios")

    # Test 1: Buy trigger with guardrail trimming
    print("\n--- Scenario 1: Buy Trigger with Guardrail Trimming ---")
    buy_price = 140.0  # 3% below anchor (150)
    test_auto_sized_order(position_id, buy_price)

    # Test 2: Sell trigger with guardrail trimming
    print("\n--- Scenario 2: Sell Trigger with Guardrail Trimming ---")
    sell_price = 160.0  # 3% above anchor (150)
    test_auto_sized_order(position_id, sell_price)

    # Test 3: No trigger (within threshold)
    print("\n--- Scenario 3: No Trigger (Within Threshold) ---")
    no_trigger_price = 155.0  # Within ±3% of anchor (150)
    test_auto_sized_order(position_id, no_trigger_price)

    # Test 4: Auto-rebalancing (drift outside guardrails)
    print("\n--- Scenario 4: Auto-Rebalancing (Drift Outside Guardrails) ---")
    # First, let's create a position that's outside guardrails
    # This would require modifying the position to have extreme allocation
    print("Note: Auto-rebalancing would trigger if position drifts outside 25%-75% bounds")


def test_order_validation(position_id: str) -> None:
    """Test order validation scenarios."""
    print_section("Testing Order Validation")

    # Test 1: Order below minimum notional
    print("\n--- Scenario 1: Order Below Minimum Notional ---")
    # This would require a very small price movement to trigger a tiny order
    tiny_price = 150.01  # Very small movement
    test_auto_sized_order(position_id, tiny_price)

    # Test 2: Market hours validation
    print("\n--- Scenario 2: Market Hours Validation ---")
    print("Note: Market hours validation is implemented but simplified")
    print("In production, this would check actual market hours")


def demonstrate_order_sizing_formula(position_id: str) -> None:
    """Demonstrate the order sizing formula with detailed calculations."""
    print_section("Order Sizing Formula Demonstration")

    # Get current position
    response = requests.get(f"{BASE_URL}/positions/{position_id}")
    if response.status_code != 200:
        print("Error getting position details")
        return

    position = response.json()
    anchor_price = position["anchor_price"]
    current_qty = position["qty"]
    current_cash = position["cash"]
    rebalance_ratio = position["order_policy"]["rebalance_ratio"]

    print("Position Details:")
    print(f"  Ticker: {position['ticker']}")
    print(f"  Current Qty: {current_qty}")
    print(f"  Current Cash: ${current_cash:.2f}")
    print(f"  Anchor Price: ${anchor_price:.2f}")
    print(f"  Rebalance Ratio: {rebalance_ratio}")

    # Test different price scenarios
    test_prices = [140.0, 150.0, 160.0]

    for price in test_prices:
        print(f"\n--- Price: ${price:.2f} ---")

        # Calculate raw order size using the formula
        asset_value = current_qty * price
        total_value = asset_value + current_cash

        # Formula: ΔQ_raw = (P_anchor / P) × r × ((A + C) / P)
        raw_qty = (anchor_price / price) * rebalance_ratio * (total_value / price)

        print(f"  Asset Value: ${asset_value:.2f}")
        print(f"  Total Value: ${total_value:.2f}")
        print(f"  Raw Qty (formula): {raw_qty:.2f}")

        # Test the actual evaluation
        evaluation = test_trigger_detection(position_id, price)
        if evaluation.get("order_proposal"):
            proposal = evaluation["order_proposal"]
            print(f"  Actual Raw Qty: {proposal['raw_qty']:.2f}")
            print(f"  Trimmed Qty: {proposal['trimmed_qty']:.2f}")
            print(f"  Notional: ${proposal['notional']:.2f}")
            print(f"  Commission: ${proposal['commission']:.2f}")
            print(f"  Trimming Reason: {proposal['trimming_reason']}")


def main():
    """Run the Phase 2 demo."""
    print("Phase 2 Demo: Advanced Order Sizing & Guardrails")
    print("=" * 60)

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

    # Create position
    position_id = create_position()
    if not position_id:
        print("Failed to create position. Exiting.")
        return

    # Set anchor price
    set_anchor_price(position_id, 150.0)

    # Demonstrate order sizing formula
    demonstrate_order_sizing_formula(position_id)

    # Test guardrail scenarios
    test_guardrail_scenarios(position_id)

    # Test order validation
    test_order_validation(position_id)

    print_section("Demo Complete")
    print("Phase 2 implementation includes:")
    print("✅ Complete order sizing formula")
    print("✅ Guardrail trimming logic")
    print("✅ Auto-rebalancing capability")
    print("✅ Enhanced order validation")
    print("✅ Auto-sized order submission API")
    print("\nNext steps: Market data integration and dividend handling")


if __name__ == "__main__":
    main()

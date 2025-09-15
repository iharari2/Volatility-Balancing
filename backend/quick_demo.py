#!/usr/bin/env python3
"""
Quick Interactive Demo
=====================

A simple interactive demo for testing the volatility trading system.
"""

import requests
import json

BASE_URL = "http://localhost:8000/v1"


def create_position():
    """Create a new position."""
    data = {"ticker": "AAPL", "qty": 0, "cash": 10000}
    response = requests.post(f"{BASE_URL}/positions", json=data)
    return response.json()


def set_anchor(position_id, price):
    """Set anchor price."""
    response = requests.post(f"{BASE_URL}/positions/{position_id}/anchor", params={"price": price})
    return response.json()


def evaluate(position_id, price):
    """Evaluate position at given price."""
    response = requests.post(
        f"{BASE_URL}/positions/{position_id}/evaluate", params={"current_price": price}
    )
    return response.json()


def show_events(position_id):
    """Show all events for position."""
    response = requests.get(f"{BASE_URL}/positions/{position_id}/events")
    return response.json()


def main():
    print("🚀 Quick Volatility Trading Demo")
    print("=" * 40)

    # Create position
    print("Creating position...")
    pos = create_position()
    position_id = pos["id"]
    print(f"✅ Position created: {position_id}")

    # Set anchor
    anchor_price = 150.0
    print(f"Setting anchor price to ${anchor_price}...")
    set_anchor(position_id, anchor_price)
    print("✅ Anchor price set")

    print(f"\nTesting triggers (anchor: ${anchor_price}):")
    print(f"Buy trigger: ≤ ${anchor_price * 0.97:.2f}")
    print(f"Sell trigger: ≥ ${anchor_price * 1.03:.2f}")

    # Test different prices
    test_prices = [145, 152, 155, 140, 160]

    for price in test_prices:
        result = evaluate(position_id, price)
        trigger = "🚨 TRIGGER" if result["trigger_detected"] else "✅ No trigger"
        print(f"  ${price}: {trigger} - {result['reasoning']}")

    # Show events
    print(f"\n📋 Events ({len(show_events(position_id)['events'])} total):")
    events = show_events(position_id)["events"]
    for event in events[-3:]:  # Show last 3 events
        print(f"  {event['type']}: {event['message']}")


if __name__ == "__main__":
    main()


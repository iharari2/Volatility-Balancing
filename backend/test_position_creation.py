#!/usr/bin/env python3
"""
Test script to verify market data and position creation functionality.
"""

import requests


def test_market_data_and_position_creation():
    """Test the complete flow from market data to position creation."""

    print("🧪 Testing Market Data and Position Creation Flow")
    print("=" * 50)

    # Test market data API
    print("\n1. Testing market data API...")
    try:
        price_response = requests.get("http://localhost:8000/v1/market/price/AAPL")
        print(f"   Status: {price_response.status_code}")

        if price_response.status_code == 200:
            price_data = price_response.json()
            current_price = price_data["price"]
            print(f"   ✅ Current AAPL Price: ${current_price}")
            print(f"   Source: {price_data['source']}")
            print(f"   Market Hours: {price_data['is_market_hours']}")
        else:
            print(f"   ❌ Market data API failed: {price_response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error fetching market data: {e}")
        return False

    # Test position creation
    print("\n2. Testing position creation...")
    try:
        investment_amount = 10000
        shares = investment_amount / current_price

        position_data = {
            "ticker": "AAPL",
            "qty": shares,
            "cash": investment_amount,
            "anchor_price": current_price,
            "order_policy": {
                "min_qty": 0,
                "min_notional": 100,
                "lot_size": 0,
                "qty_step": 0,
                "action_below_min": "hold",
                "trigger_threshold_pct": 0.02,
                "rebalance_ratio": 0.5,
                "commission_rate": 0.001,
                "allow_after_hours": True,
            },
            "guardrails": {
                "min_stock_alloc_pct": 0.1,
                "max_stock_alloc_pct": 0.9,
                "max_orders_per_day": 5,
            },
            "withholding_tax_rate": 0.25,
        }

        pos_response = requests.post("http://localhost:8000/v1/positions", json=position_data)
        print(f"   Status: {pos_response.status_code}")

        if pos_response.status_code in [200, 201]:
            position = pos_response.json()
            print("   ✅ Position created successfully!")
            print(f"   Position ID: {position['id']}")
            print(f"   Ticker: {position['ticker']}")
            print(f"   Shares: {shares:.4f}")
            print(f"   Cash: ${investment_amount:,.2f}")
            print(f"   Anchor Price: ${current_price:.2f}")
            return True
        else:
            print(f"   ❌ Position creation failed: {pos_response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error creating position: {e}")
        return False


if __name__ == "__main__":
    success = test_market_data_and_position_creation()

    if success:
        print("\n🎉 All tests passed! Market data and position creation are working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")

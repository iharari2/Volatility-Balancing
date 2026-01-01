#!/usr/bin/env python3
"""
Create sample data for testing Excel export functionality
"""

import requests
from datetime import datetime, timezone


def create_sample_data():
    """Create sample data for testing"""
    base_url = "http://localhost:8001"

    print("🔧 Creating Sample Data for Excel Export Testing")
    print("=" * 60)

    # 1. Create a position
    print("\n1. Creating sample position...")
    try:
        position_data = {
            "ticker": "AAPL",
            "qty": 100.0,
            "cash": 25000.0,
            "anchor_price": 150.0,
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

        response = requests.post(f"{base_url}/v1/positions", json=position_data)
        if response.status_code in [200, 201]:
            position = response.json()
            print(f"   ✅ Position created: {position['id']}")
            position_id = position["id"]
        else:
            print(f"   ❌ Failed to create position: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error creating position: {e}")
        return False

    # 2. Create some trades
    print("\n2. Creating sample trades...")
    try:
        trades_data = [
            {
                "position_id": position_id,
                "ticker": "AAPL",
                "qty": 50.0,
                "price": 148.50,
                "side": "buy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "commission": 0.50,
            },
            {
                "position_id": position_id,
                "ticker": "AAPL",
                "qty": 25.0,
                "price": 152.30,
                "side": "sell",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "commission": 0.25,
            },
        ]

        for trade in trades_data:
            response = requests.post(f"{base_url}/v1/trades", json=trade)
            if response.status_code in [200, 201]:
                print(f"   ✅ Trade created: {trade['side']} {trade['qty']} @ ${trade['price']}")
            else:
                print(f"   ⚠️  Trade creation failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error creating trades: {e}")

    # 3. Create some orders
    print("\n3. Creating sample orders...")
    try:
        orders_data = [
            {
                "position_id": position_id,
                "ticker": "AAPL",
                "qty": 30.0,
                "price": 151.00,
                "side": "buy",
                "status": "filled",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "position_id": position_id,
                "ticker": "AAPL",
                "qty": 15.0,
                "price": 153.50,
                "side": "sell",
                "status": "pending",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]

        for order in orders_data:
            response = requests.post(f"{base_url}/v1/orders", json=order)
            if response.status_code in [200, 201]:
                print(
                    f"   ✅ Order created: {order['side']} {order['qty']} @ ${order['price']} ({order['status']})"
                )
            else:
                print(f"   ⚠️  Order creation failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error creating orders: {e}")

    print("\n✅ Sample data creation complete!")
    print(f"   Position ID: {position_id}")
    print("   Now you can test Excel export functionality!")

    return True


if __name__ == "__main__":
    create_sample_data()

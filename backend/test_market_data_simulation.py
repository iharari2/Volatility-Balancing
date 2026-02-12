#!/usr/bin/env python3
"""
Test script for market data storage and simulation features.
"""

import requests
from datetime import datetime, timedelta


def test_market_data_storage():
    """Test market data storage and retrieval."""
    print("🧪 Testing Market Data Storage...")

    base_url = "http://localhost:8000/v1"

    # Test 1: Get current market price
    print("\n1. Testing current market price...")
    try:
        response = requests.get(f"{base_url}/market/price/AAPL")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AAPL Price: ${data['price']:.2f}")
            print(f"   Source: {data['source']}")
            print(f"   Market Hours: {data['is_market_hours']}")
            print(f"   Fresh: {data['is_fresh']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Get market status
    print("\n2. Testing market status...")
    try:
        response = requests.get(f"{base_url}/market/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Market Open: {data['is_open']}")
            print(f"   Timezone: {data['timezone']}")
            if data["next_open"]:
                print(f"   Next Open: {data['next_open']}")
            if data["next_close"]:
                print(f"   Next Close: {data['next_close']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Get volatility data
    print("\n3. Testing volatility data...")
    try:
        response = requests.get(f"{base_url}/simulation/volatility/AAPL?window_minutes=60")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AAPL Volatility (60min): {data['volatility']:.4f}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_historical_data():
    """Test historical data fetching."""
    print("\n🧪 Testing Historical Data...")

    base_url = "http://localhost:8000/v1"

    # Test historical data for last 5 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)

    print(
        f"\n1. Fetching historical data for AAPL from {start_date.date()} to {end_date.date()}..."
    )
    try:
        response = requests.get(
            f"{base_url}/market/historical/AAPL",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "market_hours_only": True,
            },
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Historical Data Points: {data['data_points']}")
            print(f"   Ticker: {data['ticker']}")
            print(f"   Market Hours Only: {data['market_hours_only']}")

            if data["price_data"]:
                first_price = data["price_data"][0]
                last_price = data["price_data"][-1]
                print(f"   First Price: ${first_price['price']:.2f} at {first_price['timestamp']}")
                print(f"   Last Price: ${last_price['price']:.2f} at {last_price['timestamp']}")

                # Calculate price change
                price_change = last_price["price"] - first_price["price"]
                price_change_pct = (price_change / first_price["price"]) * 100
                print(f"   Price Change: ${price_change:.2f} ({price_change_pct:.2f}%)")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_simulation():
    """Test trading simulation."""
    print("\n🧪 Testing Trading Simulation...")

    base_url = "http://localhost:8000/v1"

    # Test simulation for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print(f"\n1. Running simulation for AAPL from {start_date.date()} to {end_date.date()}...")

    # Position configuration
    position_config = {
        "trigger_threshold_pct": 0.03,  # 3%
        "rebalance_ratio": 1.6667,
        "commission_rate": 0.0001,  # 0.01%
        "min_notional": 100.0,
        "allow_after_hours": False,
        "guardrails": {
            "min_stock_alloc_pct": 0.25,  # 25%
            "max_stock_alloc_pct": 0.75,  # 75%
        },
    }

    try:
        response = requests.post(
            f"{base_url}/simulation/run",
            params={
                "ticker": "AAPL",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "initial_cash": 10000.0,
                "include_after_hours": False,
            },
            json=position_config,
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Simulation completed!")
            print(f"   Ticker: {data['ticker']}")
            print(f"   Trading Days: {data['total_trading_days']}")

            # Algorithm performance
            algo = data["algorithm"]
            print("\n📈 Algorithm Performance:")
            print(f"   Trades: {algo['trades']}")
            print(f"   P&L: ${algo['pnl']:.2f}")
            print(f"   Return: {algo['return_pct']:.2f}%")
            print(f"   Volatility: {algo['volatility']:.4f}")
            print(f"   Sharpe Ratio: {algo['sharpe_ratio']:.4f}")
            print(f"   Max Drawdown: {algo['max_drawdown']:.2f}%")

            # Buy & Hold performance
            buy_hold = data["buy_hold"]
            print("\n📊 Buy & Hold Performance:")
            print(f"   P&L: ${buy_hold['pnl']:.2f}")
            print(f"   Return: {buy_hold['return_pct']:.2f}%")
            print(f"   Volatility: {buy_hold['volatility']:.4f}")
            print(f"   Sharpe Ratio: {buy_hold['sharpe_ratio']:.4f}")
            print(f"   Max Drawdown: {buy_hold['max_drawdown']:.2f}%")

            # Comparison
            comparison = data["comparison"]
            print("\n⚖️  Comparison:")
            print(f"   Excess Return: {comparison['excess_return']:.2f}%")
            print(f"   Alpha: {comparison['alpha']:.2f}%")
            print(f"   Beta: {comparison['beta']:.4f}")
            print(f"   Information Ratio: {comparison['information_ratio']:.4f}")

            # Trade log (show first few trades)
            if data["trade_log"]:
                print("\n📋 Trade Log (showing first 5 trades):")
                for i, trade in enumerate(data["trade_log"][:5]):
                    print(
                        f"   {i+1}. {trade['timestamp']}: {trade['side']} {trade['qty']:.2f} @ ${trade['price']:.2f}"
                    )

                if len(data["trade_log"]) > 5:
                    print(f"   ... and {len(data['trade_log']) - 5} more trades")

        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_position_with_market_data():
    """Test position evaluation with market data."""
    print("\n🧪 Testing Position with Market Data...")

    base_url = "http://localhost:8000/v1"

    # Create a position
    print("\n1. Creating position...")
    try:
        position_data = {
            "ticker": "AAPL",
            "qty": 100.0,
            "order_policy": {
                "trigger_threshold_pct": 0.03,
                "rebalance_ratio": 1.6667,
                "commission_rate": 0.0001,
                "min_notional": 100.0,
                "allow_after_hours": False,
            },
        }

        response = requests.post(f"{base_url}/positions", json=position_data)
        if response.status_code in [200, 201]:
            data = response.json()
            position_id = data["id"]
            print(f"✅ Position created: {position_id}")

            # Set anchor price
            print("\n2. Setting anchor price...")
            anchor_response = requests.post(
                f"{base_url}/positions/{position_id}/anchor?price=150.0"
            )
            if anchor_response.status_code == 200:
                print("✅ Anchor price set to $150.00")

                # Evaluate with market data
                print("\n3. Evaluating with market data...")
                eval_response = requests.post(f"{base_url}/positions/{position_id}/evaluate/market")
                if eval_response.status_code == 200:
                    eval_data = eval_response.json()
                    print("✅ Evaluation completed!")
                    print(f"   Current Price: ${eval_data.get('current_price', 'N/A')}")
                    print(f"   Anchor Price: ${eval_data.get('anchor_price', 'N/A')}")
                    print(f"   Trigger Detected: {eval_data.get('trigger_detected', False)}")
                    print(f"   Reasoning: {eval_data.get('reasoning', 'N/A')}")

                    if eval_data.get("market_data"):
                        market_data = eval_data["market_data"]
                        print(f"   Market Data Source: {market_data.get('source', 'N/A')}")
                        print(f"   Market Hours: {market_data.get('is_market_hours', 'N/A')}")
                        print(f"   Fresh: {market_data.get('is_fresh', 'N/A')}")
                        print(f"   Inline: {market_data.get('is_inline', 'N/A')}")
                else:
                    print(
                        f"❌ Evaluation error: {eval_response.status_code} - {eval_response.text}"
                    )
            else:
                print(
                    f"❌ Anchor price error: {anchor_response.status_code} - {anchor_response.text}"
                )
        else:
            print(f"❌ Position creation error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests."""
    print("🚀 Starting Market Data & Simulation Tests")
    print("=" * 50)

    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/v1/healthz")
        if response.status_code != 200:
            print("❌ Server is not running. Please start the server first.")
            return
    except Exception:
        print("❌ Server is not running. Please start the server first.")
        return

    # Run tests
    test_market_data_storage()
    test_historical_data()
    test_simulation()
    test_position_with_market_data()

    print("\n" + "=" * 50)
    print("✅ All tests completed!")


if __name__ == "__main__":
    main()

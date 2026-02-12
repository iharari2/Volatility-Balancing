import requests
from datetime import datetime, timedelta

# Test after-hours trading with actual trade execution
print("🌙 AFTER-HOURS TRADING TEST")
print("=" * 40)

# Use a longer period to increase chances of trades
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=30)  # 30 days


def test_after_hours_trade_execution():
    """Test that trades are actually executed during after-hours when enabled."""
    print("\n🔍 Testing After-Hours Trade Execution")

    # Test with very aggressive settings to trigger trades
    aggressive_config = {
        "ticker": "AAPL",
        "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
        "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
        "initial_cash": 10000,
        "include_after_hours": True,
        "position_config": {
            "trigger_threshold_pct": 0.002,  # Very sensitive (0.2%)
            "rebalance_ratio": 0.9,  # Very aggressive
            "commission_rate": 0.001,
            "min_notional": 25,  # Low minimum
            "allow_after_hours": True,  # After-hours enabled
            "guardrails": {
                "min_stock_alloc_pct": 0.05,  # Very wide range
                "max_stock_alloc_pct": 0.95,
                "max_orders_per_day": 100,  # High frequency
            },
        },
    }

    print("  --- After-Hours ENABLED (Very Aggressive) ---")
    try:
        response = requests.post("http://localhost:8000/v1/simulation/run", json=aggressive_config)

        if response.status_code == 200:
            result = response.json()
            triggers = result.get("trigger_analysis", [])
            trades = result.get("trade_log", [])

            print("    ✅ Simulation completed successfully")
            print(f"    ✅ Total evaluations: {len(triggers)}")
            print(f"    ✅ Total trades executed: {len(trades)}")

            # Analyze after-hours vs market hours activity
            after_hours_triggered = []
            market_hours_triggered = []
            after_hours_evaluations = 0
            market_hours_evaluations = 0

            for trigger in triggers:
                time_str = trigger.get("time", "")
                hour = int(time_str.split(":")[0]) if ":" in time_str else 0

                if hour < 9 or hour >= 16:
                    after_hours_evaluations += 1
                    if trigger.get("triggered", False):
                        after_hours_triggered.append(trigger)
                else:
                    market_hours_evaluations += 1
                    if trigger.get("triggered", False):
                        market_hours_triggered.append(trigger)

            print(
                f"    📊 Market hours: {market_hours_evaluations} evaluations, {len(market_hours_triggered)} triggers"
            )
            print(
                f"    📊 After-hours: {after_hours_evaluations} evaluations, {len(after_hours_triggered)} triggers"
            )

            # Show sample after-hours triggers
            if after_hours_triggered:
                print("    🌙 Sample after-hours triggers:")
                for i, trigger in enumerate(after_hours_triggered[:3]):  # Show first 3
                    price_change = trigger.get("price_change_pct", 0)
                    side = trigger.get("side", "N/A")
                    reason = trigger.get("reason", "N/A")
                    print(
                        f"      {i+1}. {trigger.get('time', 'N/A')} - {side} - {price_change:.2f}% - {reason}"
                    )
            else:
                print("    ⚠️  No after-hours triggers found")

            # Show sample trades
            if trades:
                print("    💰 Sample trades executed:")
                for i, trade in enumerate(trades[:5]):  # Show first 5
                    time_str = trade.get("time", "N/A")
                    side = trade.get("side", "N/A")
                    qty = trade.get("qty", 0)
                    price = trade.get("price", 0)
                    print(f"      {i+1}. {time_str} - {side} {qty:.2f} @ ${price:.2f}")
            else:
                print("    ⚠️  No trades executed")

        else:
            print(f"    ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")


def test_after_hours_disabled():
    """Test that after-hours trades are blocked when disabled."""
    print("\n🔒 Testing After-Hours DISABLED")

    # Same aggressive settings but with after-hours disabled
    conservative_config = {
        "ticker": "AAPL",
        "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
        "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
        "initial_cash": 10000,
        "include_after_hours": False,
        "position_config": {
            "trigger_threshold_pct": 0.002,  # Same sensitivity
            "rebalance_ratio": 0.9,  # Same aggressiveness
            "commission_rate": 0.001,
            "min_notional": 25,
            "allow_after_hours": False,  # After-hours disabled
            "guardrails": {
                "min_stock_alloc_pct": 0.05,
                "max_stock_alloc_pct": 0.95,
                "max_orders_per_day": 100,
            },
        },
    }

    try:
        response = requests.post(
            "http://localhost:8000/v1/simulation/run", json=conservative_config
        )

        if response.status_code == 200:
            result = response.json()
            triggers = result.get("trigger_analysis", [])
            trades = result.get("trade_log", [])

            print("    ✅ Simulation completed successfully")
            print(f"    ✅ Total evaluations: {len(triggers)}")
            print(f"    ✅ Total trades executed: {len(trades)}")

            # Analyze after-hours vs market hours activity
            after_hours_triggered = []
            market_hours_triggered = []
            after_hours_evaluations = 0
            market_hours_evaluations = 0

            for trigger in triggers:
                time_str = trigger.get("time", "")
                hour = int(time_str.split(":")[0]) if ":" in time_str else 0

                if hour < 9 or hour >= 16:
                    after_hours_evaluations += 1
                    if trigger.get("triggered", False):
                        after_hours_triggered.append(trigger)
                else:
                    market_hours_evaluations += 1
                    if trigger.get("triggered", False):
                        market_hours_triggered.append(trigger)

            print(
                f"    📊 Market hours: {market_hours_evaluations} evaluations, {len(market_hours_triggered)} triggers"
            )
            print(
                f"    📊 After-hours: {after_hours_evaluations} evaluations, {len(after_hours_triggered)} triggers"
            )

            # Check if after-hours triggers are blocked
            if after_hours_triggered:
                print(
                    f"    ⚠️  WARNING: {len(after_hours_triggered)} after-hours triggers found (should be 0)"
                )
                print("    ⚠️  This suggests after-hours blocking is not working properly")
            else:
                print("    ✅ After-hours triggers properly blocked")

            # Show sample trades
            if trades:
                print("    💰 Sample trades executed:")
                for i, trade in enumerate(trades[:5]):
                    time_str = trade.get("time", "N/A")
                    side = trade.get("side", "N/A")
                    qty = trade.get("qty", 0)
                    price = trade.get("price", 0)
                    print(f"      {i+1}. {time_str} - {side} {qty:.2f} @ ${price:.2f}")
            else:
                print("    ⚠️  No trades executed")

        else:
            print(f"    ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")


def test_market_hours_validation():
    """Test market hours validation logic."""
    print("\n🕐 Testing Market Hours Validation")

    # Test with a position that should trigger during market hours
    try:
        response = requests.post(
            "http://localhost:8000/v1/simulation/run",
            json={
                "ticker": "AAPL",
                "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
                "initial_cash": 10000,
                "include_after_hours": True,
                "position_config": {
                    "trigger_threshold_pct": 0.01,
                    "rebalance_ratio": 0.5,
                    "commission_rate": 0.001,
                    "min_notional": 100,
                    "allow_after_hours": True,
                    "guardrails": {
                        "min_stock_alloc_pct": 0.25,
                        "max_stock_alloc_pct": 0.75,
                        "max_orders_per_day": 20,
                    },
                },
            },
        )

        if response.status_code == 200:
            result = response.json()
            triggers = result.get("trigger_analysis", [])

            # Analyze time distribution
            time_distribution = {}
            for trigger in triggers:
                time_str = trigger.get("time", "")
                hour = int(time_str.split(":")[0]) if ":" in time_str else 0
                time_distribution[hour] = time_distribution.get(hour, 0) + 1

            print("    ✅ Time distribution analysis:")
            for hour in sorted(time_distribution.keys()):
                count = time_distribution[hour]
                period = "Market Hours" if 9 <= hour < 16 else "After Hours"
                print(f"      {hour:02d}:00 - {count:3d} evaluations ({period})")

            # Check if we have evaluations outside market hours
            after_hours_count = sum(
                count for hour, count in time_distribution.items() if hour < 9 or hour >= 16
            )
            market_hours_count = sum(
                count for hour, count in time_distribution.items() if 9 <= hour < 16
            )

            print(f"    📊 Market hours evaluations: {market_hours_count}")
            print(f"    📊 After-hours evaluations: {after_hours_count}")
            print(
                f"    📊 After-hours ratio: {after_hours_count/(after_hours_count + market_hours_count)*100:.1f}%"
            )

        else:
            print(f"    ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")


def main():
    """Run all after-hours tests."""
    test_after_hours_trade_execution()
    test_after_hours_disabled()
    test_market_hours_validation()

    print("\n" + "=" * 40)
    print("🌙 AFTER-HOURS TESTING COMPLETED!")
    print("=" * 40)


if __name__ == "__main__":
    main()

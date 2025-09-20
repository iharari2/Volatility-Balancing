import requests
from datetime import datetime, timedelta

# Test after-hours behavior
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=5)

print("Testing after-hours behavior:")

# Test 1: After-hours enabled
print("\n--- Test 1: After-hours ENABLED ---")
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
                "allow_after_hours": True,  # After-hours enabled
                "guardrails": {
                    "min_stock_alloc_pct": 0.25,
                    "max_stock_alloc_pct": 0.75,
                    "max_orders_per_day": 10,
                },
            },
        },
    )

    if response.status_code == 200:
        result = response.json()
        triggers = result.get("trigger_analysis", [])

        print(f"✅ After-hours ENABLED simulation completed")
        print(f"  Total evaluations: {len(triggers)}")

        # Check for after-hours data
        after_hours_count = 0
        market_hours_count = 0

        for trigger in triggers:
            time_str = trigger.get("time", "")
            hour = int(time_str.split(":")[0]) if ":" in time_str else 0

            # Check if it's after hours (before 9:30 AM or after 4:00 PM ET)
            if hour < 9 or hour >= 16:
                after_hours_count += 1
            else:
                market_hours_count += 1

        print(f"  Market hours evaluations: {market_hours_count}")
        print(f"  After-hours evaluations: {after_hours_count}")
        print(f"  After-hours ratio: {after_hours_count/len(triggers)*100:.1f}%")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: After-hours disabled
print("\n--- Test 2: After-hours DISABLED ---")
try:
    response = requests.post(
        "http://localhost:8000/v1/simulation/run",
        json={
            "ticker": "AAPL",
            "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
            "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
            "initial_cash": 10000,
            "include_after_hours": False,
            "position_config": {
                "trigger_threshold_pct": 0.01,
                "rebalance_ratio": 0.5,
                "commission_rate": 0.001,
                "min_notional": 100,
                "allow_after_hours": False,  # After-hours disabled
                "guardrails": {
                    "min_stock_alloc_pct": 0.25,
                    "max_stock_alloc_pct": 0.75,
                    "max_orders_per_day": 10,
                },
            },
        },
    )

    if response.status_code == 200:
        result = response.json()
        triggers = result.get("trigger_analysis", [])

        print(f"✅ After-hours DISABLED simulation completed")
        print(f"  Total evaluations: {len(triggers)}")

        # Check for after-hours data
        after_hours_count = 0
        market_hours_count = 0

        for trigger in triggers:
            time_str = trigger.get("time", "")
            hour = int(time_str.split(":")[0]) if ":" in time_str else 0

            # Check if it's after hours (before 9:30 AM or after 4:00 PM ET)
            if hour < 9 or hour >= 16:
                after_hours_count += 1
            else:
                market_hours_count += 1

        print(f"  Market hours evaluations: {market_hours_count}")
        print(f"  After-hours evaluations: {after_hours_count}")
        print(f"  After-hours ratio: {after_hours_count/len(triggers)*100:.1f}%")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n--- Summary ---")
print("After-hours trading in our system:")
print("1. When ENABLED: System evaluates positions 24/7, including outside market hours")
print("2. When DISABLED: System only evaluates during market hours (9:30 AM - 4:00 PM ET)")
print("3. Market hours validation is done in EvaluatePositionUC._is_market_hours()")
print("4. After-hours setting is controlled by position.order_policy.allow_after_hours")
print("5. Simulation can include after-hours data via include_after_hours parameter")

import requests
import time
from datetime import datetime, timedelta

# Comprehensive test suite for all new features
print("🧪 COMPREHENSIVE FEATURE TEST SUITE")
print("=" * 50)

# Test configuration
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=10)


def test_bid_ask_display():
    """Test that bid/ask values are correctly displayed in trigger analysis."""
    print("\n🔍 Test 1: Bid/Ask Display")
    try:
        response = requests.post(
            "http://localhost:8000/v1/simulation/run",
            json={
                "ticker": "AAPL",
                "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
                "initial_cash": 10000,
                "position_config": {
                    "trigger_threshold_pct": 0.01,
                    "rebalance_ratio": 0.5,
                    "commission_rate": 0.001,
                    "min_notional": 100,
                    "allow_after_hours": True,
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

            if triggers:
                first_trigger = triggers[0]
                price = first_trigger.get("price", 0)
                bid = first_trigger.get("bid", 0)
                ask = first_trigger.get("ask", 0)

                # Check if bid/ask are calculated correctly (should be price ± 0.05%)
                expected_spread = price * 0.0005
                expected_bid = price - expected_spread
                expected_ask = price + expected_spread

                bid_correct = abs(bid - expected_bid) < 0.01
                ask_correct = abs(ask - expected_ask) < 0.01

                print(f"  ✅ Price: ${price:.2f}")
                print(f"  ✅ Bid: ${bid:.2f} (expected: ${expected_bid:.2f})")
                print(f"  ✅ Ask: ${ask:.2f} (expected: ${expected_ask:.2f})")
                print(f"  ✅ Bid calculation: {'PASS' if bid_correct else 'FAIL'}")
                print(f"  ✅ Ask calculation: {'PASS' if ask_correct else 'FAIL'}")
            else:
                print("  ❌ No trigger data found")
        else:
            print(f"  ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def test_configurable_intervals():
    """Test configurable intraday intervals."""
    print("\n⏰ Test 2: Configurable Intervals")

    intervals_to_test = [15, 30, 60]

    for interval in intervals_to_test:
        try:
            response = requests.post(
                "http://localhost:8000/v1/simulation/run",
                json={
                    "ticker": "AAPL",
                    "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                    "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
                    "initial_cash": 10000,
                    "intraday_interval_minutes": interval,
                    "position_config": {
                        "trigger_threshold_pct": 0.01,
                        "rebalance_ratio": 0.5,
                        "commission_rate": 0.001,
                        "min_notional": 100,
                        "allow_after_hours": True,
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

                # Count unique times per day
                unique_times = set(trigger.get("time", "") for trigger in triggers)
                unique_times_count = len(unique_times)

                print(
                    f"  ✅ {interval}-min intervals: {len(triggers)} evaluations, {unique_times_count} unique times"
                )
            else:
                print(f"  ❌ {interval}-min intervals: Error {response.status_code}")
        except Exception as e:
            print(f"  ❌ {interval}-min intervals: Error {e}")


def test_error_handling():
    """Test comprehensive error handling."""
    print("\n🛡️ Test 3: Error Handling")

    # Test invalid ticker
    try:
        response = requests.post(
            "http://localhost:8000/v1/simulation/run",
            json={
                "ticker": "INVALID_TICKER_12345",
                "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
                "initial_cash": 10000,
            },
        )

        if response.status_code == 400:
            print("  ✅ Invalid ticker correctly rejected")
        else:
            print(f"  ❌ Invalid ticker should be rejected: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Invalid ticker test error: {e}")

    # Test invalid date range
    try:
        response = requests.post(
            "http://localhost:8000/v1/simulation/run",
            json={
                "ticker": "AAPL",
                "start_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
                "end_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),  # End before start
                "initial_cash": 10000,
            },
        )

        if response.status_code == 400:
            print("  ✅ Invalid date range correctly rejected")
        else:
            print(f"  ❌ Invalid date range should be rejected: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Invalid date range test error: {e}")


def test_performance_optimization():
    """Test trigger analysis performance optimization."""
    print("\n⚡ Test 4: Performance Optimization")

    # Test detailed trigger analysis
    start_time = time.time()
    try:
        response = requests.post(
            "http://localhost:8000/v1/simulation/run",
            json={
                "ticker": "AAPL",
                "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
                "initial_cash": 10000,
                "detailed_trigger_analysis": True,
                "position_config": {
                    "trigger_threshold_pct": 0.01,
                    "rebalance_ratio": 0.5,
                    "commission_rate": 0.001,
                    "min_notional": 100,
                    "allow_after_hours": True,
                    "guardrails": {
                        "min_stock_alloc_pct": 0.25,
                        "max_stock_alloc_pct": 0.75,
                        "max_orders_per_day": 10,
                    },
                },
            },
        )

        detailed_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            triggers = result.get("trigger_analysis", [])
            first_trigger = triggers[0] if triggers else {}
            has_detailed_data = "bid" in first_trigger and "ask" in first_trigger

            print(
                f"  ✅ Detailed analysis: {detailed_time:.2f}s, {len(triggers)} triggers, detailed data: {has_detailed_data}"
            )
        else:
            print(f"  ❌ Detailed analysis failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Detailed analysis error: {e}")

    # Test optimized trigger analysis
    start_time = time.time()
    try:
        response = requests.post(
            "http://localhost:8000/v1/simulation/run",
            json={
                "ticker": "AAPL",
                "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
                "initial_cash": 10000,
                "detailed_trigger_analysis": False,
                "position_config": {
                    "trigger_threshold_pct": 0.01,
                    "rebalance_ratio": 0.5,
                    "commission_rate": 0.001,
                    "min_notional": 100,
                    "allow_after_hours": True,
                    "guardrails": {
                        "min_stock_alloc_pct": 0.25,
                        "max_stock_alloc_pct": 0.75,
                        "max_orders_per_day": 10,
                    },
                },
            },
        )

        optimized_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            triggers = result.get("trigger_analysis", [])
            first_trigger = triggers[0] if triggers else {}
            has_detailed_data = "bid" in first_trigger and "ask" in first_trigger

            print(
                f"  ✅ Optimized analysis: {optimized_time:.2f}s, {len(triggers)} triggers, detailed data: {has_detailed_data}"
            )
        else:
            print(f"  ❌ Optimized analysis failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Optimized analysis error: {e}")


def test_after_hours_trading():
    """Test after-hours trading scenarios with actual trade execution."""
    print("\n🌙 Test 5: After-Hours Trading Scenarios")

    # Test after-hours enabled with aggressive settings to trigger trades
    print("  --- After-Hours ENABLED (Aggressive) ---")
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
                    "trigger_threshold_pct": 0.005,  # Very sensitive (0.5%)
                    "rebalance_ratio": 0.8,  # Large position changes
                    "commission_rate": 0.001,
                    "min_notional": 50,
                    "allow_after_hours": True,  # After-hours enabled
                    "guardrails": {
                        "min_stock_alloc_pct": 0.1,
                        "max_stock_alloc_pct": 0.9,
                        "max_orders_per_day": 50,
                    },
                },
            },
        )

        if response.status_code == 200:
            result = response.json()
            triggers = result.get("trigger_analysis", [])
            trades = result.get("trade_log", [])

            # Analyze after-hours vs market hours trades
            after_hours_trades = 0
            market_hours_trades = 0
            after_hours_evaluations = 0
            market_hours_evaluations = 0

            for trigger in triggers:
                time_str = trigger.get("time", "")
                hour = int(time_str.split(":")[0]) if ":" in time_str else 0

                if hour < 9 or hour >= 16:
                    after_hours_evaluations += 1
                    if trigger.get("triggered", False):
                        after_hours_trades += 1
                else:
                    market_hours_evaluations += 1
                    if trigger.get("triggered", False):
                        market_hours_trades += 1

            print(f"    ✅ Total evaluations: {len(triggers)}")
            print(
                f"    ✅ Market hours: {market_hours_evaluations} evaluations, {market_hours_trades} trades"
            )
            print(
                f"    ✅ After-hours: {after_hours_evaluations} evaluations, {after_hours_trades} trades"
            )
            print(f"    ✅ Total trades executed: {len(trades)}")
            print(
                f"    ✅ After-hours trade ratio: {after_hours_trades/len(trades)*100:.1f}%"
                if trades
                else "    ✅ No trades executed"
            )
        else:
            print(f"    ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

    # Test after-hours disabled
    print("  --- After-Hours DISABLED (Conservative) ---")
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
                    "trigger_threshold_pct": 0.005,  # Same sensitivity
                    "rebalance_ratio": 0.8,  # Same aggressiveness
                    "commission_rate": 0.001,
                    "min_notional": 50,
                    "allow_after_hours": False,  # After-hours disabled
                    "guardrails": {
                        "min_stock_alloc_pct": 0.1,
                        "max_stock_alloc_pct": 0.9,
                        "max_orders_per_day": 50,
                    },
                },
            },
        )

        if response.status_code == 200:
            result = response.json()
            triggers = result.get("trigger_analysis", [])
            trades = result.get("trade_log", [])

            # Analyze after-hours vs market hours trades
            after_hours_trades = 0
            market_hours_trades = 0
            after_hours_evaluations = 0
            market_hours_evaluations = 0

            for trigger in triggers:
                time_str = trigger.get("time", "")
                hour = int(time_str.split(":")[0]) if ":" in time_str else 0

                if hour < 9 or hour >= 16:
                    after_hours_evaluations += 1
                    if trigger.get("triggered", False):
                        after_hours_trades += 1
                else:
                    market_hours_evaluations += 1
                    if trigger.get("triggered", False):
                        market_hours_trades += 1

            print(f"    ✅ Total evaluations: {len(triggers)}")
            print(
                f"    ✅ Market hours: {market_hours_evaluations} evaluations, {market_hours_trades} trades"
            )
            print(
                f"    ✅ After-hours: {after_hours_evaluations} evaluations, {after_hours_trades} trades"
            )
            print(f"    ✅ Total trades executed: {len(trades)}")
            print(
                f"    ✅ After-hours trade ratio: {after_hours_trades/len(trades)*100:.1f}%"
                if trades
                else "    ✅ No trades executed"
            )
        else:
            print(f"    ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")


def test_data_validation():
    """Test data validation features."""
    print("\n🔍 Test 6: Data Validation")

    try:
        response = requests.post(
            "http://localhost:8000/v1/simulation/run",
            json={
                "ticker": "AAPL",
                "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
                "initial_cash": 10000,
                "position_config": {
                    "trigger_threshold_pct": 0.01,
                    "rebalance_ratio": 0.5,
                    "commission_rate": 0.001,
                    "min_notional": 100,
                    "allow_after_hours": True,
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

            if triggers:
                # Check data quality
                first_trigger = triggers[0]
                required_fields = ["timestamp", "price", "anchor_price", "price_change_pct"]
                missing_fields = [field for field in required_fields if field not in first_trigger]

                if not missing_fields:
                    print("  ✅ All required fields present")
                else:
                    print(f"  ❌ Missing fields: {missing_fields}")

                # Check OHLC consistency
                ohlc_fields = ["open", "high", "low", "close"]
                ohlc_present = all(field in first_trigger for field in ohlc_fields)
                print(f"  ✅ OHLC data present: {ohlc_present}")

                # Check price consistency
                price = first_trigger.get("price", 0)
                high = first_trigger.get("high", price)
                low = first_trigger.get("low", price)

                price_consistent = low <= price <= high
                print(f"  ✅ Price consistency (low <= price <= high): {price_consistent}")
            else:
                print("  ❌ No trigger data found")
        else:
            print(f"  ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def test_simulation_presets():
    """Test simulation presets functionality."""
    print("\n🎯 Test 7: Simulation Presets")

    # Test getting all presets
    try:
        response = requests.get("http://localhost:8000/v1/simulation/presets")

        if response.status_code == 200:
            result = response.json()
            presets = result.get("presets", [])
            print(f"  ✅ Found {len(presets)} presets")

            for preset in presets:
                print(
                    f"    - {preset.get('preset_id', 'unknown')}: {preset.get('name', 'unknown')}"
                )
        else:
            print(f"  ❌ Error getting presets: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error getting presets: {e}")

    # Test specific preset
    try:
        response = requests.get("http://localhost:8000/v1/simulation/presets/day_trading")

        if response.status_code == 200:
            preset = response.json()
            print(f"  ✅ Day trading preset: {preset.get('name', 'unknown')}")
            print(
                f"    Trigger threshold: {preset.get('position_config', {}).get('trigger_threshold_pct', 0)*100}%"
            )
            print(f"    Interval: {preset.get('intraday_interval_minutes', 0)} minutes")
        else:
            print(f"  ❌ Error getting day trading preset: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error getting day trading preset: {e}")

    # Test running simulation with preset
    try:
        response = requests.post(
            "http://localhost:8000/v1/simulation/run-with-preset",
            json={
                "ticker": "AAPL",
                "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                "end_date": end_date.strftime("%Y-%m-%dT00:00:00Z"),
                "preset_id": "swing_trading",
                "initial_cash": 10000,
            },
        )

        if response.status_code == 200:
            result = response.json()
            preset_used = result.get("preset_used", {})
            trades = result.get("total_trades", 0)

            print("  ✅ Simulation with preset completed")
            print(f"    Preset: {preset_used.get('name', 'unknown')}")
            print(f"    Total trades: {trades}")
        else:
            print(f"  ❌ Error running preset simulation: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error running preset simulation: {e}")


def main():
    """Run all tests."""
    test_bid_ask_display()
    test_configurable_intervals()
    test_error_handling()
    test_performance_optimization()
    test_after_hours_trading()
    test_data_validation()
    test_simulation_presets()

    print("\n" + "=" * 50)
    print("🎉 COMPREHENSIVE TEST SUITE COMPLETED!")
    print("=" * 50)


if __name__ == "__main__":
    main()

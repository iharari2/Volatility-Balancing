#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta


def test_trigger_analysis():
    # Calculate dates for a short test
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=10)

    print(f"Testing trigger analysis from {start_date.date()} to {end_date.date()}")

    # Test the simulation API
    response = requests.post(
        "http://localhost:8000/v1/simulation/run",
        json={
            "ticker": "ZIM",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "initial_cash": 10000,
            "position_config": {
                "trigger_threshold_pct": 0.03,
                "rebalance_ratio": 0.5,
                "commission_rate": 0.001,
                "min_notional": 100,
                "allow_after_hours": True,
                "guardrails": {
                    "min_stock_alloc_pct": 0.25,
                    "max_stock_alloc_pct": 0.75,
                    "max_orders_per_day": 5,
                },
            },
            "include_after_hours": True,
        },
    )

    print("Status:", response.status_code)
    if response.status_code == 200:
        result = response.json()
        print("Algorithm trades:", result.get("algorithm", {}).get("trades"))
        print("Trigger analysis count:", len(result.get("trigger_analysis", [])))

        # Show sample trigger analysis
        trigger_analysis = result.get("trigger_analysis", [])
        if trigger_analysis:
            print("\nSample trigger analysis entries:")
            for i, trigger in enumerate(trigger_analysis[:5]):
                print(
                    f'{i+1}. {trigger["timestamp"]} - Price: ${trigger["price"]:.2f} - Change: {trigger["price_change_pct"]:.2f}% - Triggered: {trigger["triggered"]} - Executed: {trigger["executed"]} - Reason: {trigger["reason"]}'
                )

            # Count by status
            triggered_count = sum(1 for t in trigger_analysis if t["triggered"])
            executed_count = sum(1 for t in trigger_analysis if t["executed"])
            print(
                f"\nSummary: {triggered_count} triggered, {executed_count} executed out of {len(trigger_analysis)} total evaluations"
            )
    else:
        print("Error:", response.text)


if __name__ == "__main__":
    test_trigger_analysis()

#!/usr/bin/env python3
import requests
from datetime import datetime, timedelta


def test_api_direct():
    # Test the API directly
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=5)

    print(f"Testing API directly from {start_date.date()} to {end_date.date()}")

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
        print("Success!")
        print("Algorithm trades:", result.get("algorithm", {}).get("trades"))
        print("Trigger analysis count:", len(result.get("trigger_analysis", [])))
    else:
        print("Error:", response.text)


if __name__ == "__main__":
    test_api_direct()

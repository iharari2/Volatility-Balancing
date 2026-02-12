#!/usr/bin/env python3
"""
Phase 4 Demo: Dividend Handling
===============================

This script demonstrates the complete Phase 4 implementation:
- Dividend announcement and tracking
- Ex-dividend date processing with anchor price adjustment
- Dividend receivable management
- Dividend payment processing
- Integration with position guardrails using effective cash

Run this after starting the server:
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

BASE_URL = "http://localhost:8000/v1"


def print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_result(title: str, result: Dict[str, Any]) -> None:
    print(f"\n{title}:")
    print(json.dumps(result, indent=2, default=str))


def create_position_with_dividend_settings() -> str:
    """Create a test position with dividend settings."""
    print_section("Creating Test Position with Dividend Settings")

    position_data = {
        "ticker": "AAPL",
        "qty": 100.0,
        "cash": 10000.0,
        "withholding_tax_rate": 0.25,  # 25% withholding tax
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
        return result["id"]
    else:
        print(f"Error creating position: {response.status_code} - {response.text}")
        return None


def announce_dividend(
    ticker: str, ex_date: datetime, pay_date: datetime, dps: float
) -> Dict[str, Any]:
    """Announce a dividend."""
    print_section(f"Announcing Dividend for {ticker}")

    dividend_data = {
        "ticker": ticker,
        "ex_date": ex_date.isoformat(),
        "pay_date": pay_date.isoformat(),
        "dps": dps,
        "currency": "USD",
        "withholding_tax_rate": 0.25,
    }

    response = requests.post(f"{BASE_URL}/dividends/announce", json=dividend_data)
    if response.status_code == 200:
        result = response.json()
        print_result("Dividend Announced", result)
        return result
    else:
        print(f"Error announcing dividend: {response.status_code} - {response.text}")
        return {}


def test_dividend_status(position_id: str) -> None:
    """Test dividend status for a position."""
    print_section("Testing Dividend Status")

    response = requests.get(f"{BASE_URL}/dividends/positions/{position_id}/status")
    if response.status_code == 200:
        result = response.json()
        print_result("Dividend Status", result)
    else:
        print(f"Error getting dividend status: {response.status_code} - {response.text}")


def test_market_dividend_info(ticker: str) -> None:
    """Test market dividend information."""
    print_section(f"Testing Market Dividend Info for {ticker}")

    response = requests.get(f"{BASE_URL}/dividends/market/{ticker}/info")
    if response.status_code == 200:
        result = response.json()
        print_result(f"Market Dividend Info for {ticker}", result)
    else:
        print(f"Error getting market dividend info: {response.status_code} - {response.text}")


def test_upcoming_dividends(ticker: str) -> None:
    """Test upcoming dividends."""
    print_section(f"Testing Upcoming Dividends for {ticker}")

    response = requests.get(f"{BASE_URL}/dividends/market/{ticker}/upcoming")
    if response.status_code == 200:
        result = response.json()
        print_result(f"Upcoming Dividends for {ticker}", result)
    else:
        print(f"Error getting upcoming dividends: {response.status_code} - {response.text}")


def simulate_ex_dividend_processing(position_id: str) -> None:
    """Simulate ex-dividend date processing."""
    print_section("Simulating Ex-Dividend Date Processing")

    # First, announce a dividend with today as ex-date
    today = datetime.now()
    pay_date = today + timedelta(days=14)
    dps = 0.82  # $0.82 per share

    # Announce dividend
    dividend = announce_dividend("AAPL", today, pay_date, dps)
    if not dividend:
        print("Failed to announce dividend")
        return

    # Process ex-dividend date
    response = requests.post(f"{BASE_URL}/dividends/positions/{position_id}/process-ex-dividend")
    if response.status_code == 200:
        result = response.json()
        print_result("Ex-Dividend Processing Result", result)

        if result.get("processed"):
            # Show position after ex-dividend processing
            pos_response = requests.get(f"{BASE_URL}/positions/{position_id}")
            if pos_response.status_code == 200:
                position = pos_response.json()
                print_result("Position After Ex-Dividend Processing", position)
    else:
        print(f"Error processing ex-dividend date: {response.status_code} - {response.text}")


def test_dividend_payment_processing(position_id: str) -> None:
    """Test dividend payment processing."""
    print_section("Testing Dividend Payment Processing")

    # First get dividend status to find receivables
    response = requests.get(f"{BASE_URL}/dividends/positions/{position_id}/status")
    if response.status_code != 200:
        print("Error getting dividend status")
        return

    status = response.json()
    pending_receivables = status.get("pending_receivables", [])

    if not pending_receivables:
        print("No pending receivables found")
        return

    # Process the first receivable
    receivable_id = pending_receivables[0]["id"]

    payment_data = {"receivable_id": receivable_id}
    response = requests.post(
        f"{BASE_URL}/dividends/positions/{position_id}/process-payment", json=payment_data
    )

    if response.status_code == 200:
        result = response.json()
        print_result("Dividend Payment Processing Result", result)

        # Show position after payment
        pos_response = requests.get(f"{BASE_URL}/positions/{position_id}")
        if pos_response.status_code == 200:
            position = pos_response.json()
            print_result("Position After Dividend Payment", position)
    else:
        print(f"Error processing dividend payment: {response.status_code} - {response.text}")


def test_effective_cash_in_guardrails(position_id: str) -> None:
    """Test that guardrails use effective cash including dividend receivable."""
    print_section("Testing Effective Cash in Guardrails")

    # Get current position
    response = requests.get(f"{BASE_URL}/positions/{position_id}")
    if response.status_code != 200:
        print("Error getting position")
        return

    position = response.json()
    print("Position Details:")
    print(f"  Cash: ${position.get('cash', 0):.2f}")
    print(f"  Dividend Receivable: ${position.get('dividend_receivable', 0):.2f}")
    print(
        f"  Effective Cash: ${position.get('cash', 0) + position.get('dividend_receivable', 0):.2f}"
    )
    print(f"  Shares: {position.get('qty', 0)}")
    print(f"  Anchor Price: ${position.get('anchor_price', 0):.2f}")

    # Test evaluation with current market price
    # This should use effective cash in guardrail calculations
    response = requests.post(f"{BASE_URL}/positions/{position_id}/evaluate/market")
    if response.status_code == 200:
        result = response.json()
        print_result("Position Evaluation with Effective Cash", result)
    else:
        print(f"Error evaluating position: {response.status_code} - {response.text}")


def demonstrate_dividend_workflow() -> None:
    """Demonstrate complete dividend workflow."""
    print_section("Complete Dividend Workflow Demonstration")

    # Step 1: Create position
    position_id = create_position_with_dividend_settings()
    if not position_id:
        print("Failed to create position")
        return

    # Step 2: Set anchor price
    response = requests.post(f"{BASE_URL}/positions/{position_id}/anchor", params={"price": 150.0})
    if response.status_code == 200:
        print_result("Anchor Price Set", response.json())

    # Step 3: Test market dividend info
    test_market_dividend_info("AAPL")

    # Step 4: Test upcoming dividends
    test_upcoming_dividends("AAPL")

    # Step 5: Test dividend status (should be empty initially)
    test_dividend_status(position_id)

    # Step 6: Simulate ex-dividend processing
    simulate_ex_dividend_processing(position_id)

    # Step 7: Test effective cash in guardrails
    test_effective_cash_in_guardrails(position_id)

    # Step 8: Test dividend payment processing
    test_dividend_payment_processing(position_id)

    # Step 9: Final dividend status
    test_dividend_status(position_id)


def main():
    """Run the Phase 4 demo."""
    print("Phase 4 Demo: Dividend Handling")
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

    # Run complete dividend workflow
    demonstrate_dividend_workflow()

    print_section("Demo Complete")
    print("Phase 4 implementation includes:")
    print("✅ Dividend announcement and tracking")
    print("✅ Ex-dividend date processing with anchor adjustment")
    print("✅ Dividend receivable management")
    print("✅ Dividend payment processing")
    print("✅ Integration with guardrails using effective cash")
    print("✅ Market data integration for dividend information")
    print("\nNext steps: Frontend integration and Excel export functionality")


if __name__ == "__main__":
    main()


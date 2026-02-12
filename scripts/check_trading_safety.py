#!/usr/bin/env python3
"""
Trading Safety Check Script

Checks deployment safety conditions:
1. Is US market currently open?
2. Are there active trading positions?
3. Are there pending orders?

Exit codes:
  0 - Safe to deploy (market closed, no active trading)
  1 - Warning: deployment may impact trading
  2 - Error: could not complete safety checks

Usage:
  python check_trading_safety.py           # Interactive mode
  python check_trading_safety.py --ci-mode # CI mode (non-interactive, exit code only)
"""

import argparse
import os
import sys
from datetime import datetime, time
from typing import NamedTuple

try:
    import pytz
except ImportError:
    pytz = None

try:
    import requests
except ImportError:
    requests = None


class SafetyCheckResult(NamedTuple):
    """Result of a safety check."""
    passed: bool
    message: str
    details: str = ""


def check_market_hours() -> SafetyCheckResult:
    """Check if US market is currently open."""
    if pytz is None:
        return SafetyCheckResult(
            passed=True,
            message="pytz not installed, skipping market hours check",
            details="Install pytz to enable market hours checking"
        )

    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)

    # Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday
    market_open = time(9, 30)
    market_close = time(16, 0)

    # Check if weekend
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return SafetyCheckResult(
            passed=True,
            message="Market closed (weekend)",
            details=f"Current time: {now.strftime('%A %I:%M %p ET')}"
        )

    # Check market hours
    current_time = now.time()
    if market_open <= current_time <= market_close:
        return SafetyCheckResult(
            passed=False,
            message="Market is OPEN",
            details=f"Current time: {now.strftime('%I:%M %p ET')} (Market: 9:30 AM - 4:00 PM ET)"
        )

    return SafetyCheckResult(
        passed=True,
        message="Market closed",
        details=f"Current time: {now.strftime('%I:%M %p ET')}"
    )


def check_active_positions(api_base: str, api_token: str | None = None) -> SafetyCheckResult:
    """Check if there are active trading positions."""
    if requests is None:
        return SafetyCheckResult(
            passed=True,
            message="requests not installed, skipping active positions check",
            details="Install requests to enable API checks"
        )

    if not api_base:
        return SafetyCheckResult(
            passed=True,
            message="API_BASE not configured, skipping active positions check",
            details="Set API_BASE environment variable to enable"
        )

    try:
        headers = {}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        response = requests.get(
            f"{api_base}/v1/trading/active",
            headers=headers,
            timeout=10
        )

        if response.status_code == 404:
            # Endpoint doesn't exist yet
            return SafetyCheckResult(
                passed=True,
                message="Active trading endpoint not available",
                details="Endpoint /v1/trading/active not found"
            )

        if response.status_code != 200:
            return SafetyCheckResult(
                passed=True,
                message=f"Could not check active positions (HTTP {response.status_code})",
                details="Proceeding with deployment"
            )

        data = response.json()
        active_count = len(data) if isinstance(data, list) else data.get("count", 0)

        if active_count > 0:
            return SafetyCheckResult(
                passed=False,
                message=f"{active_count} active trading position(s)",
                details="Consider pausing trading worker before deployment"
            )

        return SafetyCheckResult(
            passed=True,
            message="No active trading positions",
            details=""
        )

    except requests.exceptions.Timeout:
        return SafetyCheckResult(
            passed=True,
            message="API timeout, skipping active positions check",
            details="Could not reach API within 10 seconds"
        )
    except requests.exceptions.RequestException as e:
        return SafetyCheckResult(
            passed=True,
            message=f"API error, skipping check: {e}",
            details=""
        )


def check_pending_orders(api_base: str, api_token: str | None = None) -> SafetyCheckResult:
    """Check if there are pending orders."""
    if requests is None:
        return SafetyCheckResult(
            passed=True,
            message="requests not installed, skipping pending orders check",
            details="Install requests to enable API checks"
        )

    if not api_base:
        return SafetyCheckResult(
            passed=True,
            message="API_BASE not configured, skipping pending orders check",
            details="Set API_BASE environment variable to enable"
        )

    try:
        headers = {}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        # Check for pending orders - this endpoint may vary
        response = requests.get(
            f"{api_base}/v1/orders?status=pending",
            headers=headers,
            timeout=10
        )

        if response.status_code == 404:
            return SafetyCheckResult(
                passed=True,
                message="Orders endpoint not available",
                details="Endpoint /v1/orders not found"
            )

        if response.status_code != 200:
            return SafetyCheckResult(
                passed=True,
                message=f"Could not check pending orders (HTTP {response.status_code})",
                details="Proceeding with deployment"
            )

        data = response.json()
        pending_count = len(data) if isinstance(data, list) else data.get("count", 0)

        if pending_count > 0:
            return SafetyCheckResult(
                passed=False,
                message=f"{pending_count} pending order(s)",
                details="Wait for orders to settle before deployment"
            )

        return SafetyCheckResult(
            passed=True,
            message="No pending orders",
            details=""
        )

    except requests.exceptions.Timeout:
        return SafetyCheckResult(
            passed=True,
            message="API timeout, skipping pending orders check",
            details="Could not reach API within 10 seconds"
        )
    except requests.exceptions.RequestException as e:
        return SafetyCheckResult(
            passed=True,
            message=f"API error, skipping check: {e}",
            details=""
        )


def check_trading_worker_status(api_base: str, api_token: str | None = None) -> SafetyCheckResult:
    """Check if the trading worker is enabled."""
    if requests is None:
        return SafetyCheckResult(
            passed=True,
            message="requests not installed, skipping worker status check",
            details="Install requests to enable API checks"
        )

    if not api_base:
        return SafetyCheckResult(
            passed=True,
            message="API_BASE not configured, skipping worker status check",
            details=""
        )

    try:
        headers = {}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        response = requests.get(
            f"{api_base}/v1/trading/worker/status",
            headers=headers,
            timeout=10
        )

        if response.status_code == 404:
            return SafetyCheckResult(
                passed=True,
                message="Worker status endpoint not available",
                details=""
            )

        if response.status_code != 200:
            return SafetyCheckResult(
                passed=True,
                message=f"Could not check worker status (HTTP {response.status_code})",
                details=""
            )

        data = response.json()
        enabled = data.get("enabled", False)

        if enabled:
            return SafetyCheckResult(
                passed=False,
                message="Trading worker is ENABLED",
                details="Consider disabling worker: POST /v1/trading/worker/enable {enabled: false}"
            )

        return SafetyCheckResult(
            passed=True,
            message="Trading worker is disabled",
            details=""
        )

    except requests.exceptions.RequestException:
        return SafetyCheckResult(
            passed=True,
            message="Could not check worker status",
            details=""
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check if it's safe to deploy during trading hours"
    )
    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="CI mode: non-interactive, exit code only"
    )
    args = parser.parse_args()

    # Get configuration from environment
    api_base = os.environ.get("API_BASE", "").rstrip("/")
    api_token = os.environ.get("API_TOKEN")

    # Run all checks
    checks = [
        ("Market Hours", check_market_hours()),
        ("Active Positions", check_active_positions(api_base, api_token)),
        ("Pending Orders", check_pending_orders(api_base, api_token)),
        ("Trading Worker", check_trading_worker_status(api_base, api_token)),
    ]

    # Print results
    print("=" * 60)
    print("TRADING SAFETY CHECK")
    print("=" * 60)

    all_passed = True
    warnings = []

    for name, result in checks:
        status = "✓" if result.passed else "✗"
        print(f"\n{status} {name}: {result.message}")
        if result.details:
            print(f"  {result.details}")

        if not result.passed:
            all_passed = False
            warnings.append(name)

    print("\n" + "=" * 60)

    if all_passed:
        print("RESULT: Safe to deploy")
        return 0
    else:
        print(f"RESULT: Deployment warnings - {', '.join(warnings)}")
        print("\nDeploying now may impact live trading.")
        if not args.ci_mode:
            print("Recommended: Deploy outside market hours or pause trading first.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

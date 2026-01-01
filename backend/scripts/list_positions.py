#!/usr/bin/env python3
"""
List all positions in the system to find position IDs.

Usage:
    python scripts/list_positions.py
    python scripts/list_positions.py --ticker AAPL
    python scripts/list_positions.py --ticker ZIM
"""

import sys
import os
import argparse

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.di import container


def list_all_positions(ticker_filter=None):
    """List all positions, optionally filtered by ticker."""
    print("=" * 80)
    print("LISTING ALL POSITIONS")
    print("=" * 80)

    tenant_id = "default"
    portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)

    all_positions = []
    for portfolio in portfolios:
        positions = container.positions.list_all(
            tenant_id=tenant_id,
            portfolio_id=portfolio.id,
        )
        for pos in positions:
            if ticker_filter:
                if pos.asset_symbol.upper() == ticker_filter.upper():
                    all_positions.append((portfolio, pos))
            else:
                all_positions.append((portfolio, pos))

    if not all_positions:
        print("\n❌ No positions found")
        if ticker_filter:
            print(f"   (filtered by ticker: {ticker_filter})")
        return

    print(f"\nFound {len(all_positions)} position(s):\n")

    for i, (portfolio, position) in enumerate(all_positions, 1):
        print(f"{i}. Position ID: {position.id}")
        print(f"   Portfolio: {portfolio.name} ({portfolio.id})")
        print(f"   Ticker: {position.asset_symbol}")
        print(f"   Quantity: {position.qty}")
        print(f"   Cash: ${position.cash:.2f}")
        print(
            f"   Anchor Price: ${position.anchor_price:.2f}"
            if position.anchor_price
            else "   Anchor Price: ❌ NOT SET"
        )
        print(f"   Portfolio State: {portfolio.trading_state}")
        print()

    print("=" * 80)
    print("\nTo diagnose a position, run:")
    print("  python scripts/diagnose_trading_issue.py <position_id>")
    print("\nExample:")
    if all_positions:
        first_pos = all_positions[0][1]
        print(f"  python scripts/diagnose_trading_issue.py {first_pos.id}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="List all positions in the system")
    parser.add_argument("--ticker", type=str, help="Filter by ticker symbol (e.g., AAPL, ZIM)")
    args = parser.parse_args()

    list_all_positions(ticker_filter=args.ticker)


if __name__ == "__main__":
    main()

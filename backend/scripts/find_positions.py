#!/usr/bin/env python3
"""
Find positions by searching the database directly.

This script will:
1. Check SQLite database directly
2. List all positions regardless of tenant_id
3. Show position details including ticker, anchor_price, etc.
"""

import sys
import os
import sqlite3

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.di import container


def find_positions_in_db():
    """Find positions by querying database directly."""
    print("=" * 80)
    print("SEARCHING FOR POSITIONS IN DATABASE")
    print("=" * 80)

    # Try to get database path from container
    db_path = None

    # Check if we can get the database path from the positions repo
    if hasattr(container.positions, "_sf"):
        # SQLAlchemy session factory - try to get engine URL
        try:
            engine = container.positions._sf.kw.get("bind")
            if engine:
                url = str(engine.url)
                if "sqlite" in url:
                    # Extract path from sqlite:///path/to/db
                    db_path = url.replace("sqlite:///", "")
                    if not os.path.isabs(db_path):
                        # Relative path, make it absolute from backend directory
                        db_path = os.path.join(os.path.dirname(__file__), "..", db_path)
        except Exception:
            pass

    # Try common database locations
    if not db_path or not os.path.exists(db_path):
        common_paths = [
            "vb.sqlite",
            "vb_test.sqlite",
            "../vb.sqlite",
            "../vb_test.sqlite",
            "backend/vb.sqlite",
            "backend/vb_test.sqlite",
        ]
        for path in common_paths:
            full_path = os.path.join(os.path.dirname(__file__), "..", path)
            if os.path.exists(full_path):
                db_path = full_path
                break

    if not db_path or not os.path.exists(db_path):
        print("\n❌ Could not find database file")
        print("   Tried common locations but database not found")
        print("\n💡 Try using the API instead:")
        print("   curl http://localhost:8000/v1/portfolios")
        return

    print(f"\n✅ Found database: {db_path}\n")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all positions
        cursor.execute("""
            SELECT 
                id, 
                tenant_id, 
                portfolio_id, 
                asset_symbol, 
                qty, 
                cash, 
                anchor_price, 
                avg_cost,
                created_at
            FROM positions
            ORDER BY created_at DESC
        """)

        positions = cursor.fetchall()

        if not positions:
            print("❌ No positions found in database")
            conn.close()
            return

        print(f"Found {len(positions)} position(s) in database:\n")
        print("-" * 80)

        for pos in positions:
            (
                pos_id,
                tenant_id,
                portfolio_id,
                asset_symbol,
                qty,
                cash,
                anchor_price,
                avg_cost,
                created_at,
            ) = pos
            print(f"Position ID: {pos_id}")
            print(f"  Tenant ID: {tenant_id}")
            print(f"  Portfolio ID: {portfolio_id}")
            print(f"  Ticker: {asset_symbol}")
            print(f"  Quantity: {qty}")
            print(f"  Cash: ${cash:.2f}" if cash else "  Cash: $0.00")
            print(
                f"  Anchor Price: ${anchor_price:.2f}"
                if anchor_price
                else "  Anchor Price: ❌ NOT SET"
            )
            print(f"  Avg Cost: ${avg_cost:.2f}" if avg_cost else "  Avg Cost: N/A")
            print(f"  Created: {created_at}")
            print("-" * 80)
            print()

        # Get portfolio info
        print("\n" + "=" * 80)
        print("PORTFOLIO INFORMATION")
        print("=" * 80)

        cursor.execute("""
            SELECT DISTINCT portfolio_id, tenant_id
            FROM positions
        """)

        portfolio_ids = cursor.fetchall()

        for portfolio_id, tenant_id in portfolio_ids:
            cursor.execute(
                """
                SELECT id, name, trading_state, trading_hours_policy
                FROM portfolios
                WHERE id = ? AND tenant_id = ?
            """,
                (portfolio_id, tenant_id),
            )

            portfolio = cursor.fetchone()
            if portfolio:
                p_id, name, trading_state, trading_hours_policy = portfolio
                print(f"\nPortfolio: {name} ({p_id})")
                print(f"  Tenant ID: {tenant_id}")
                print(f"  Trading State: {trading_state}")
                print(f"  Trading Hours Policy: {trading_hours_policy}")

        conn.close()

        print("\n" + "=" * 80)
        print("\nTo diagnose a position, run:")
        if positions:
            first_pos_id = positions[0][0]
            print(f"  python scripts/diagnose_trading_issue.py {first_pos_id}")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error reading database: {e}")
        import traceback

        traceback.print_exc()


def find_positions_via_api():
    """Try to find positions via the application container."""
    print("\n" + "=" * 80)
    print("SEARCHING VIA APPLICATION CONTAINER")
    print("=" * 80)

    try:
        # Try to get all portfolios
        tenant_ids = ["default", "test", "demo"]

        for tenant_id in tenant_ids:
            try:
                portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
                print(f"\nTenant ID: {tenant_id}")
                print(f"  Found {len(portfolios)} portfolio(s)")

                for portfolio in portfolios:
                    print(f"\n  Portfolio: {portfolio.name} ({portfolio.id})")
                    print(f"    Trading State: {portfolio.trading_state}")

                    try:
                        positions = container.positions.list_all(
                            tenant_id=tenant_id,
                            portfolio_id=portfolio.id,
                        )
                        print(f"    Positions: {len(positions)}")

                        for pos in positions:
                            print(
                                f"      - {pos.id}: {pos.asset_symbol} (qty={pos.qty}, cash=${pos.cash:.2f}, anchor=${pos.anchor_price or 0:.2f})"
                            )
                    except Exception as e:
                        print(f"    Error listing positions: {e}")

            except Exception as e:
                print(f"  Error with tenant {tenant_id}: {e}")
                continue

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main function."""
    # First try database directly
    find_positions_in_db()

    # Then try via application
    find_positions_via_api()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test Step 1: Position Discovery"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure SQL persistence is enabled
if not os.getenv("APP_PERSISTENCE"):
    os.environ["APP_PERSISTENCE"] = "sql"
if not os.getenv("APP_EVENTS"):
    os.environ["APP_EVENTS"] = "sql"
if not os.getenv("APP_AUTO_CREATE"):
    os.environ["APP_AUTO_CREATE"] = "true"
if not os.getenv("SQL_URL"):
    os.environ["SQL_URL"] = "sqlite:///./vb.sqlite"

from app.di import container


def test_position_discovery(position_id: str) -> bool:
    """
    Test finding a position and its associated tenant/portfolio IDs.

    Returns:
        True if position found, False otherwise
    """
    print("=" * 80)
    print("Testing Step 1: Position Discovery")
    print("=" * 80)
    print(f"Looking for position: {position_id}")
    print()

    # Step 1: Try to query database directly first (more reliable)
    position = None
    tenant_id = None
    portfolio_id = None
    portfolio = None

    # First, try to get tenant_id and portfolio_id from database directly
    print("Attempting direct database query...")
    try:
        from infrastructure.persistence.sql.positions_repo_sql import SQLPositionsRepo
        from sqlalchemy import text

        print(f"  Position repo type: {type(container.positions).__name__}")
        print(f"  Is SQLPositionsRepo: {isinstance(container.positions, SQLPositionsRepo)}")

        if isinstance(container.positions, SQLPositionsRepo) and hasattr(
            container.positions, "_sf"
        ):
            print("  Using SQLPositionsRepo with session factory")
            session_factory = container.positions._sf
            with session_factory() as s:
                try:
                    # Query without tenant restriction to find position
                    raw_sql = text(
                        """
                        SELECT tenant_id, portfolio_id FROM positions
                        WHERE id = :position_id
                        LIMIT 1
                        """
                    )
                    result = s.execute(raw_sql, {"position_id": position_id})
                    row = result.fetchone()
                    if row:
                        tenant_id, portfolio_id = row[0], row[1]
                        print(
                            f"  ✅ Found in database: tenant={tenant_id}, portfolio={portfolio_id}"
                        )
                        # Now get the position using the repo
                        position = container.positions.get(
                            tenant_id=tenant_id,
                            portfolio_id=portfolio_id,
                            position_id=position_id,
                        )
                        if position:
                            print("  ✅ Position retrieved via repo")
                            # Get portfolio
                            if container.portfolio_repo:
                                portfolio = container.portfolio_repo.get(tenant_id, portfolio_id)
                                if portfolio:
                                    print(f"  ✅ Portfolio retrieved: {portfolio.name}")
                        else:
                            print("  ⚠️  Position not found via repo even though it exists in DB")
                    else:
                        print(f"  ⚠️  Position {position_id} not found in database")
                except Exception as e:
                    print(f"  ❌ Database query failed: {e}")
                    import traceback

                    traceback.print_exc()
        else:
            print("  ⚠️  Not using SQLPositionsRepo or missing _sf attribute")
    except (ImportError, AttributeError) as e:
        print(f"  ⚠️  Could not use direct database query: {e}")
        import traceback

        traceback.print_exc()

    # Fallback: Search across portfolios (original method)
    if not position:
        if container.portfolio_repo:
            search_tenant_id = "default"
            portfolios = container.portfolio_repo.list_all(tenant_id=search_tenant_id)
            print(f"Found {len(portfolios)} portfolio(s) to search")

            for p in portfolios:
                print(f"  Checking portfolio: {p.id} ({p.name})")
                pos = container.positions.get(
                    tenant_id=search_tenant_id,
                    portfolio_id=p.id,
                    position_id=position_id,
                )
                if pos:
                    position = pos
                    tenant_id = search_tenant_id
                    portfolio_id = p.id
                    portfolio = p
                    print(f"  ✅ Found position in portfolio {p.id}")
                    break
        else:
            if not position:
                print("❌ No portfolio_repo available and position not found")
                return False

    # Verify results
    if not position:
        print(f"❌ Position {position_id} NOT FOUND in any portfolio")
        return False

    print()
    print("✅ Position Discovery Results:")
    print(f"   Position ID: {position.id}")
    print(f"   Tenant ID: {tenant_id}")
    print(f"   Portfolio ID: {portfolio_id}")
    print(f"   Portfolio Name: {portfolio.name if portfolio else 'N/A'}")
    print(f"   Asset: {position.asset_symbol}")
    print(f"   Quantity: {position.qty}")
    print(f"   Cash: ${position.cash:.2f}")
    print(
        f"   Anchor Price: ${position.anchor_price:.2f}"
        if position.anchor_price
        else "   Anchor Price: None"
    )

    # Verify portfolio state
    if portfolio:
        print(f"   Portfolio State: {portfolio.trading_state}")
        if portfolio.trading_state != "RUNNING":
            print(f"   ⚠️  WARNING: Portfolio state is {portfolio.trading_state}, not RUNNING")
            print("      Positions in this portfolio may not be eligible for trading")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_step1_position_discovery.py <position_id>")
        print("Example: python test_step1_position_discovery.py pos_f0c83651")
        sys.exit(1)

    position_id = sys.argv[1]
    success = test_position_discovery(position_id)
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Test Step 3: Configuration Loading"""

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


def test_config_loading(position_id: str) -> bool:
    """
    Test loading trigger, guardrail, and order policy configurations.

    Returns:
        True if configs loaded successfully, False otherwise
    """
    print("=" * 80)
    print("Testing Step 3: Configuration Loading")
    print("=" * 80)
    print(f"Loading configs for position: {position_id}")
    print()

    # First, find the position to get tenant_id and portfolio_id
    # Use direct database query (same as Step 1)
    tenant_id = None
    portfolio_id = None

    try:
        from infrastructure.persistence.sql.positions_repo_sql import SQLPositionsRepo
        from sqlalchemy import text

        if isinstance(container.positions, SQLPositionsRepo) and hasattr(
            container.positions, "_sf"
        ):
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
                            f"Found position in database: tenant={tenant_id}, portfolio={portfolio_id}"
                        )
                except Exception as e:
                    print(f"  Database query failed: {e}")
    except (ImportError, AttributeError) as e:
        print(f"  Could not use direct database query: {e}")

    # Fallback: Search across portfolios
    if not tenant_id or not portfolio_id:
        search_tenant_id = "default"
        if container.portfolio_repo:
            portfolios = container.portfolio_repo.list_all(tenant_id=search_tenant_id)
            for p in portfolios:
                pos = container.positions.get(
                    tenant_id=search_tenant_id,
                    portfolio_id=p.id,
                    position_id=position_id,
                )
                if pos:
                    tenant_id = search_tenant_id
                    portfolio_id = p.id
                    break

    if not tenant_id or not portfolio_id:
        print(f"❌ Could not find position {position_id}")
        return False

    print(f"Found position in tenant={tenant_id}, portfolio={portfolio_id}")
    print()

    # Test trigger config
    try:
        print("Loading trigger config...")
        trigger_config = container.trigger_config_provider(tenant_id, portfolio_id, position_id)
        print("✅ Trigger Config:")
        print(f"   Up Threshold: {trigger_config.up_threshold_pct}%")
        print(f"   Down Threshold: {trigger_config.down_threshold_pct}%")
        print(f"   Type: {type(trigger_config.up_threshold_pct).__name__}")
    except Exception as e:
        print(f"❌ Failed to load trigger config: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test guardrail config
    try:
        print()
        print("Loading guardrail config...")
        guardrail_config = container.guardrail_config_provider(tenant_id, portfolio_id, position_id)
        print("✅ Guardrail Config:")
        print(f"   Min Stock %: {guardrail_config.min_stock_pct}%")
        print(f"   Max Stock %: {guardrail_config.max_stock_pct}%")
        print(f"   Max Trade %: {guardrail_config.max_trade_pct_of_position}%")
        print(f"   Type: {type(guardrail_config.min_stock_pct).__name__}")
    except Exception as e:
        print(f"❌ Failed to load guardrail config: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test order policy config
    try:
        print()
        print("Loading order policy config...")
        order_policy_config = container.order_policy_config_provider(
            tenant_id, portfolio_id, position_id
        )
        print("✅ Order Policy Config:")
        print(f"   Rebalance Ratio: {order_policy_config.rebalance_ratio}")
        print(f"   Commission Rate: {order_policy_config.commission_rate}%")
        print(f"   Type: {type(order_policy_config.rebalance_ratio).__name__}")
    except Exception as e:
        print(f"❌ Failed to load order policy config: {e}")
        import traceback

        traceback.print_exc()
        return False

    print()
    print("✅ All configs loaded successfully")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_step3_config_loading.py <position_id>")
        print("Example: python test_step3_config_loading.py pos_f0c83651")
        sys.exit(1)

    position_id = sys.argv[1]
    success = test_config_loading(position_id)
    sys.exit(0 if success else 1)

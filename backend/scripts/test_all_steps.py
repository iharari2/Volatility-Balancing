#!/usr/bin/env python3
"""Test All Steps: End-to-End Test"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_step1_position_discovery import test_position_discovery
from test_step2_market_data import test_market_data
from test_step3_config_loading import test_config_loading
from test_step4_position_evaluation import test_position_evaluation


def test_all_steps(position_id: str) -> bool:
    """
    Test all steps in sequence for a position.

    Returns:
        True if all steps pass, False otherwise
    """
    print("=" * 80)
    print("END-TO-END TEST: All Steps")
    print("=" * 80)
    print()

    [
        ("Step 1: Position Discovery", lambda: test_position_discovery(position_id)),
        ("Step 2: Market Data", None),  # Will be called after Step 1
        ("Step 3: Config Loading", lambda: test_config_loading(position_id)),
        ("Step 4: Position Evaluation", lambda: test_position_evaluation(position_id)),
    ]

    # Get ticker from Step 1
    from app.di import container

    search_tenant_id = "default"
    ticker = None

    if container.portfolio_repo:
        portfolios = container.portfolio_repo.list_all(tenant_id=search_tenant_id)
        for p in portfolios:
            pos = container.positions.get(
                tenant_id=search_tenant_id,
                portfolio_id=p.id,
                position_id=position_id,
            )
            if pos:
                ticker = pos.asset_symbol
                break

    if not ticker:
        print(f"❌ Could not find position {position_id}")
        return False

    # Run Step 1
    if not test_position_discovery(position_id):
        print("❌ Step 1 failed, aborting")
        return False

    print()

    # Run Step 2
    if not test_market_data(ticker):
        print("❌ Step 2 failed, aborting")
        return False

    print()

    # Run Step 3
    if not test_config_loading(position_id):
        print("❌ Step 3 failed, aborting")
        return False

    print()

    # Run Step 4
    if not test_position_evaluation(position_id):
        print("❌ Step 4 failed, aborting")
        return False

    print()
    print("=" * 80)
    print("✅ ALL STEPS PASSED")
    print("=" * 80)
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_all_steps.py <position_id>")
        print("Example: python test_all_steps.py pos_f0c83651")
        sys.exit(1)

    position_id = sys.argv[1]
    success = test_all_steps(position_id)
    sys.exit(0 if success else 1)

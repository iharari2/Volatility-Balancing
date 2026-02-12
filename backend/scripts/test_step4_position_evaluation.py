#!/usr/bin/env python3
"""Test Step 4: Position Evaluation"""

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


def test_position_evaluation(position_id: str, current_price: float = None) -> bool:
    """
    Test evaluating a position for triggers and order proposals.

    Returns:
        True if evaluation completed successfully, False otherwise
    """
    print("=" * 80)
    print("Testing Step 4: Position Evaluation")
    print("=" * 80)
    print(f"Evaluating position: {position_id}")
    print()

    # Step 1: Find position - use direct database query (same as Step 1)
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

    # Step 2: Get position and current price if not provided
    position = container.positions.get(tenant_id, portfolio_id, position_id)
    if not position:
        print(f"❌ Could not load position {position_id}")
        return False

    print(f"✅ Found position in tenant={tenant_id}, portfolio={portfolio_id}")
    print(
        f"Position: {position.asset_symbol}, Qty={position.qty:.4f}, Cash=${position.cash:.2f}, Anchor=${position.anchor_price:.2f}"
    )
    print()

    if current_price is None:
        price_data = container.market_data.get_reference_price(position.asset_symbol)
        if not price_data:
            print(f"❌ Could not fetch market data for {position.asset_symbol}")
            return False
        current_price = float(price_data.price)
        print(
            f"Current price: ${current_price:.2f} (source: {price_data.source}, fresh: {price_data.is_fresh})"
        )
    else:
        print(f"Using provided price: ${current_price:.2f}")

    print()

    # Step 3: Run evaluation
    try:
        eval_uc = container.get_evaluate_position_uc()
        print("Running evaluation...")
        evaluation_result = eval_uc.evaluate(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            current_price=current_price,
        )

        print("✅ Evaluation Results:")
        print(f"   Trigger Detected: {evaluation_result.get('trigger_detected', False)}")
        print(f"   Action: {evaluation_result.get('action', 'HOLD')}")
        print(f"   Reasoning: {evaluation_result.get('reasoning', 'N/A')}")

        order_proposal = evaluation_result.get("order_proposal")
        if order_proposal:
            print()
            print("   Order Proposal:")
            print(f"      Side: {order_proposal.get('side')}")
            print(f"      Raw Qty: {order_proposal.get('raw_qty', 0):.4f}")
            print(f"      Trimmed Qty: {order_proposal.get('trimmed_qty', 0):.4f}")
            print(f"      Notional: ${order_proposal.get('notional', 0):.2f}")
            print(f"      Commission: ${order_proposal.get('commission', 0):.2f}")

            validation = order_proposal.get("validation", {})
            print(f"      Validation Valid: {validation.get('valid', False)}")
            if validation.get("rejections"):
                print(f"      Rejections: {validation.get('rejections')}")
        else:
            print("   No order proposal")

        return True

    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_step4_position_evaluation.py <position_id> [current_price]")
        print("Example: python test_step4_position_evaluation.py pos_f0c83651")
        print("Example: python test_step4_position_evaluation.py pos_f0c83651 275.50")
        sys.exit(1)

    position_id = sys.argv[1]
    current_price = float(sys.argv[2]) if len(sys.argv) > 2 else None
    success = test_position_evaluation(position_id, current_price)
    sys.exit(0 if success else 1)

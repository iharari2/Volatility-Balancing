#!/usr/bin/env python3
"""
Diagnostic script to identify why trades are not executing.

Run this script to check:
1. If positions exist and have anchor_price set
2. If portfolios are in RUNNING state
3. If continuous trading service is actually running
4. If there are any errors in the evaluation
5. If triggers are being detected
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.di import container
from application.services.continuous_trading_service import get_continuous_trading_service
from application.use_cases.evaluate_position_uc import EvaluatePositionUC


def check_position(position_id: str):
    """Check if position exists and has required configuration."""
    print(f"\n{'='*60}")
    print(f"Checking Position: {position_id}")
    print(f"{'='*60}")

    # Search for position - try multiple tenant IDs
    position = None
    tenant_id = None
    portfolio_id = None
    portfolio = None

    # Try common tenant IDs
    tenant_ids_to_try = ["default", "test", "demo"]

    for tid in tenant_ids_to_try:
        try:
            portfolios = container.portfolio_repo.list_all(tenant_id=tid)
            for p in portfolios:
                pos = container.positions.get(
                    tenant_id=tid,
                    portfolio_id=p.id,
                    position_id=position_id,
                )
                if pos:
                    position = pos
                    tenant_id = tid
                    portfolio_id = p.id
                    portfolio = p
                    break
            if position:
                break
        except Exception:
            continue  # Try next tenant_id

    # If still not found, try searching all positions
    if not position:
        print("⚠️  Position not found in common tenant IDs, searching all positions...")
        for tid in tenant_ids_to_try:
            try:
                portfolios = container.portfolio_repo.list_all(tenant_id=tid)
                for p in portfolios:
                    positions = container.positions.list_all(
                        tenant_id=tid,
                        portfolio_id=p.id,
                    )
                    for pos in positions:
                        if pos.id == position_id:
                            position = pos
                            tenant_id = tid
                            portfolio_id = p.id
                            portfolio = p
                            break
                    if position:
                        break
                if position:
                    break
            except Exception:
                continue

    if not position:
        print(f"❌ Position {position_id} NOT FOUND in any portfolio")
        print("\n💡 Tip: Run 'python scripts/list_positions.py' to see all available positions")
        print("   Or: python scripts/list_positions.py --ticker AAPL")
        print("   Or: python scripts/list_positions.py --ticker ZIM")
        return False

    print("✅ Position found:")
    print(f"   - Tenant ID: {tenant_id}")
    print(f"   - Portfolio ID: {portfolio_id}")
    print(f"   - Asset Symbol: {position.asset_symbol}")
    print(f"   - Quantity: {position.qty}")
    print(f"   - Cash: {position.cash}")
    print(f"   - Anchor Price: {position.anchor_price}")
    print(f"   - Avg Cost: {position.avg_cost}")

    # Check anchor price
    if not position.anchor_price:
        print("\n❌ CRITICAL: Position has NO anchor_price set!")
        print("   → Trades cannot execute without anchor_price")
        print("   → Fix: Set anchor_price on the position")
        return False
    else:
        print(f"✅ Anchor price is set: ${position.anchor_price:.2f}")

    # Check portfolio state
    if portfolio:
        print("\n✅ Portfolio found:")
        print(f"   - Portfolio ID: {portfolio.id}")
        print(f"   - Name: {portfolio.name}")
        print(f"   - Trading State: {portfolio.trading_state}")

        if portfolio.trading_state != "RUNNING":
            print("\n❌ CRITICAL: Portfolio is NOT in RUNNING state!")
            print(f"   → Current state: {portfolio.trading_state}")
            print("   → Fix: Set portfolio trading_state to 'RUNNING'")
            return False
        else:
            print("✅ Portfolio is in RUNNING state")

    # Check continuous trading service
    service = get_continuous_trading_service()
    status = service.get_status(position_id)

    if status:
        print("\n✅ Continuous Trading Service Status:")
        print(f"   - Is Running: {status.is_running}")
        print(f"   - Is Paused: {status.is_paused}")
        print(f"   - Total Checks: {status.total_checks}")
        print(f"   - Total Trades: {status.total_trades}")
        print(f"   - Total Errors: {status.total_errors}")
        print(f"   - Last Error: {status.last_error}")
        print(f"   - Last Check: {status.last_check}")

        if status.total_errors > 0:
            print(f"\n⚠️  WARNING: {status.total_errors} errors occurred")
            if status.last_error:
                print(f"   Last error: {status.last_error}")
    else:
        print("\n⚠️  Continuous trading service is NOT running for this position")
        print(f"   → Fix: Start trading using /v1/trading/start/{position_id}")

    # Try to evaluate the position
    print(f"\n{'='*60}")
    print("Testing Evaluation")
    print(f"{'='*60}")

    try:
        # Get current market price
        price_data = container.market_data.get_price(position.asset_symbol, force_refresh=True)
        if not price_data or not price_data.price:
            print(f"❌ Could not fetch market price for {position.asset_symbol}")
            return False

        current_price = price_data.price
        print(f"✅ Current market price: ${current_price:.2f}")

        # Create evaluation UC
        eval_uc = EvaluatePositionUC(
            positions=container.positions,
            events=container.events,
            market_data=container.market_data,
            clock=container.clock,
            portfolio_repo=container.portfolio_repo,
        )

        # Evaluate
        print("\n🔍 Running evaluation...")
        evaluation = eval_uc.evaluate(tenant_id, portfolio_id, position_id, current_price)

        print("✅ Evaluation completed:")
        print(f"   - Trigger Detected: {evaluation.get('trigger_detected', False)}")
        print(f"   - Trigger Type: {evaluation.get('trigger_type')}")
        print(f"   - Reasoning: {evaluation.get('reasoning', 'N/A')}")

        order_proposal = evaluation.get("order_proposal")
        if order_proposal:
            print("\n✅ Order Proposal Generated:")
            print(f"   - Side: {order_proposal.get('side')}")
            print(f"   - Quantity: {order_proposal.get('trimmed_qty', 0)}")
            print(f"   - Commission: {order_proposal.get('commission', 0)}")

            validation = order_proposal.get("validation", {})
            print(f"   - Validation Valid: {validation.get('valid', False)}")
            if validation.get("rejections"):
                print(f"   - Rejections: {validation.get('rejections')}")
        else:
            print("\n⚠️  No order proposal generated")
            if not evaluation.get("trigger_detected"):
                print("   → Reason: No trigger detected")
                print(f"   → Current price: ${current_price:.2f}")
                print(f"   → Anchor price: ${position.anchor_price:.2f}")
                price_change_pct = (
                    (current_price - position.anchor_price) / position.anchor_price
                ) * 100
                print(f"   → Price change: {price_change_pct:.2f}%")

        return True

    except Exception as e:
        print("\n❌ ERROR during evaluation:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main diagnostic function."""
    if len(sys.argv) < 2:
        print("Usage: python diagnose_trading_issue.py <position_id> [position_id2 ...]")
        print("\nExample:")
        print("  python diagnose_trading_issue.py pos_abc123 pos_def456")
        sys.exit(1)

    position_ids = sys.argv[1:]

    print("=" * 60)
    print("TRADING ISSUE DIAGNOSTIC TOOL")
    print("=" * 60)

    all_ok = True
    for position_id in position_ids:
        if not check_position(position_id):
            all_ok = False

    print(f"\n{'='*60}")
    if all_ok:
        print("✅ All checks passed - trades should be executing")
        print("\nIf trades are still not executing, check:")
        print("  1. Are triggers actually firing? (price must move > threshold)")
        print("  2. Are guardrails blocking trades?")
        print("  3. Check application logs for runtime errors")
        print("  4. Verify market data is being fetched correctly")
    else:
        print("❌ Issues found - see details above")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

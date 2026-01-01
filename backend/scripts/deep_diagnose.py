#!/usr/bin/env python3
"""
Deep diagnostic to find why trades aren't executing.
"""

import sys
import os
import sqlite3

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.di import container
from application.services.continuous_trading_service import get_continuous_trading_service
from application.use_cases.evaluate_position_uc import EvaluatePositionUC


def check_portfolio_persistence():
    """Check if portfolio state persists."""
    db_path = os.path.join(os.path.dirname(__file__), "..", "vb.sqlite")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("PORTFOLIO STATE PERSISTENCE CHECK")
    print("=" * 80)

    # Check current state
    cursor.execute("SELECT id, name, trading_state FROM portfolios")
    portfolios = cursor.fetchall()

    for p_id, name, state in portfolios:
        print(f"\nPortfolio: {name} ({p_id})")
        print(f"  Current DB state: {state}")

        # Fix it
        if state != "RUNNING":
            print("  → Fixing to RUNNING...")
            cursor.execute("UPDATE portfolios SET trading_state = 'RUNNING' WHERE id = ?", (p_id,))
            conn.commit()
            print("  ✅ Updated in database")

            # Verify it stuck
            cursor.execute("SELECT trading_state FROM portfolios WHERE id = ?", (p_id,))
            new_state = cursor.fetchone()[0]
            print(f"  Verified state: {new_state}")

            if new_state != "RUNNING":
                print("  ❌ State didn't persist! Something is resetting it.")
            else:
                print("  ✅ State persisted correctly")

    conn.close()


def test_evaluation(position_id):
    """Test evaluation directly."""
    print("\n" + "=" * 80)
    print(f"TESTING EVALUATION FOR {position_id}")
    print("=" * 80)

    # Find position
    position = None
    tenant_id = "default"
    portfolio_id = None

    portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
    for p in portfolios:
        pos = container.positions.get(tenant_id, p.id, position_id)
        if pos:
            position = pos
            portfolio_id = p.id
            break

    if not position:
        print(f"❌ Position {position_id} not found")
        return

    print("✅ Position found:")
    print(f"   Ticker: {position.asset_symbol}")
    print(f"   Anchor: ${position.anchor_price:.2f}")
    print(f"   Cash: ${position.cash:.2f}")
    print(f"   Qty: {position.qty:.4f}")

    # Get current price
    try:
        price_data = container.market_data.get_price(position.asset_symbol, force_refresh=True)
        if not price_data or not price_data.price:
            print(f"❌ Could not get price for {position.asset_symbol}")
            return

        current_price = price_data.price
        print(f"\n✅ Current market price: ${current_price:.2f}")

        # Calculate price change
        if position.anchor_price:
            price_change_pct = (
                (current_price - float(position.anchor_price)) / float(position.anchor_price)
            ) * 100
            print(f"   Price change from anchor: {price_change_pct:.2f}%")

            # Check trigger thresholds (assuming 3%)
            threshold = 3.0
            if price_change_pct <= -threshold:
                print(f"   ✅ BUY trigger should fire (down {abs(price_change_pct):.2f}%)")
            elif price_change_pct >= threshold:
                print(f"   ✅ SELL trigger should fire (up {price_change_pct:.2f}%)")
            else:
                print(
                    f"   ⚠️  No trigger (need >{threshold}% change, got {abs(price_change_pct):.2f}%)"
                )

        # Test evaluation
        print("\n🔍 Running evaluation...")
        eval_uc = EvaluatePositionUC(
            positions=container.positions,
            events=container.events,
            market_data=container.market_data,
            clock=container.clock,
            portfolio_repo=container.portfolio_repo,
        )

        result = eval_uc.evaluate(tenant_id, portfolio_id, position_id, current_price)

        print("\n✅ Evaluation result:")
        print(f"   Trigger detected: {result.get('trigger_detected', False)}")
        print(f"   Trigger type: {result.get('trigger_type')}")
        print(f"   Reasoning: {result.get('reasoning', 'N/A')}")

        order_proposal = result.get("order_proposal")
        if order_proposal:
            print("\n✅ Order proposal generated:")
            print(f"   Side: {order_proposal.get('side')}")
            print(f"   Qty: {order_proposal.get('trimmed_qty', 0)}")

            validation = order_proposal.get("validation", {})
            print(f"   Validation valid: {validation.get('valid', False)}")
            if validation.get("rejections"):
                print(f"   Rejections: {validation.get('rejections')}")
        else:
            print("\n⚠️  No order proposal generated")

    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        import traceback

        traceback.print_exc()


def check_trading_service():
    """Check continuous trading service."""
    print("\n" + "=" * 80)
    print("CONTINUOUS TRADING SERVICE CHECK")
    print("=" * 80)

    service = get_continuous_trading_service()
    active = service.list_active()

    if not active:
        print("❌ No positions in trading service")
        print("\n💡 Start trading:")
        print("   curl -X POST http://localhost:8000/v1/trading/start/pos_f0c83651")
    else:
        print(f"✅ {len(active)} position(s) in trading service:")
        for pos_id, status in active.items():
            print(f"\n   Position: {pos_id}")
            print(f"      Checks: {status.total_checks}")
            print(f"      Trades: {status.total_trades}")
            print(f"      Errors: {status.total_errors}")
            if status.last_error:
                print(f"      ⚠️  Last Error: {status.last_error}")
            if status.last_check:
                print(f"      Last Check: {status.last_check}")


def check_recent_activity():
    """Check recent events and trades."""
    print("\n" + "=" * 80)
    print("RECENT ACTIVITY CHECK")
    print("=" * 80)

    db_path = os.path.join(os.path.dirname(__file__), "..", "vb.sqlite")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check events table schema
    cursor.execute("PRAGMA table_info(events)")
    columns = [row[1] for row in cursor.fetchall()]
    timestamp_col = "ts" if "ts" in columns else ("timestamp" if "timestamp" in columns else None)

    if timestamp_col:
        cursor.execute(f"""
            SELECT position_id, type, {timestamp_col}, message 
            FROM events 
            WHERE position_id IN ('pos_f0c83651', 'pos_c955d000')
            ORDER BY {timestamp_col} DESC 
            LIMIT 10
        """)

        events = cursor.fetchall()
        if events:
            print(f"\n📋 Recent Events ({len(events)}):")
            for event in events[:10]:
                if len(event) >= 3:
                    print(f"   [{event[2]}] {event[0]}: {event[1]}")
                    if len(event) >= 4 and event[3]:
                        msg = event[3][:60]
                        print(f"      {msg}")
        else:
            print("\n⚠️  No recent events found")
            print("   → This suggests evaluation cycles aren't running")

    # Check trades
    cursor.execute("""
        SELECT position_id, side, qty, price, executed_at 
        FROM trades 
        WHERE position_id IN ('pos_f0c83651', 'pos_c955d000')
        ORDER BY executed_at DESC 
        LIMIT 5
    """)

    trades = cursor.fetchall()
    if trades:
        print(f"\n💼 Recent Trades ({len(trades)}):")
        for trade in trades:
            print(f"   [{trade[4]}] {trade[0]}: {trade[1]} {trade[2]:.4f} @ ${trade[3]:.2f}")
    else:
        print("\n⚠️  No trades found")

    conn.close()


def main():
    """Main diagnostic."""
    # 1. Check portfolio persistence
    check_portfolio_persistence()

    # 2. Test evaluation
    test_evaluation("pos_f0c83651")

    # 3. Check trading service
    check_trading_service()

    # 4. Check recent activity
    check_recent_activity()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nIf portfolio state keeps reverting:")
    print("  1. Check if there's code that resets it on startup")
    print("  2. Check if portfolio creation sets it to NOT_CONFIGURED")
    print("  3. Manually set it via SQL and see if it persists")
    print("\nIf no triggers are firing:")
    print("  1. Check price movement vs threshold (need >3% typically)")
    print("  2. Check trigger configuration")
    print(
        "  3. Manually trigger a cycle: curl -X POST 'http://localhost:8000/v1/trading/cycle?position_id=pos_f0c83651'"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()

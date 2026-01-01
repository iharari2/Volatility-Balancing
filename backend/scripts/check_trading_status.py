#!/usr/bin/env python3
"""
Quick check of trading status and portfolio state.
"""

import sys
import os
import sqlite3

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from application.services.continuous_trading_service import get_continuous_trading_service


def check_all():
    """Check everything."""
    print("=" * 80)
    print("TRADING STATUS CHECK")
    print("=" * 80)

    # Check portfolio state
    db_path = os.path.join(os.path.dirname(__file__), "..", "vb.sqlite")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, trading_state FROM portfolios")
    portfolios = cursor.fetchall()

    print("\n📁 Portfolio States:")
    for p_id, name, state in portfolios:
        status = "✅" if state == "RUNNING" else "❌"
        print(f"  {status} {name} ({p_id}): {state}")
        if state != "RUNNING":
            print(f"     → Fix: python scripts/fix_portfolio_state.py --portfolio-id {p_id}")

    # Check trading service status
    print("\n🔄 Continuous Trading Service:")
    service = get_continuous_trading_service()
    active = service.list_active()

    if not active:
        print("  ❌ No positions are actively trading")
    else:
        for position_id, status in active.items():
            print(f"\n  Position: {position_id}")
            print(f"    Checks: {status.total_checks}")
            print(f"    Trades: {status.total_trades}")
            print(f"    Errors: {status.total_errors}")
            if status.last_error:
                print(f"    ⚠️  Last Error: {status.last_error}")
            if status.last_check:
                print(f"    Last Check: {status.last_check}")

    # Check recent events
    print("\n📋 Recent Events (last 5):")
    cursor.execute("""
        SELECT position_id, type, created_at, message 
        FROM events 
        WHERE position_id IN ('pos_f0c83651', 'pos_c955d000')
        ORDER BY created_at DESC 
        LIMIT 5
    """)

    events = cursor.fetchall()
    if events:
        for pos_id, event_type, created_at, message in events:
            print(f"  [{created_at}] {pos_id}: {event_type}")
            if message:
                print(f"    {message[:80]}")
    else:
        print("  ⚠️  No recent events found")

    # Check trades
    print("\n💼 Trades:")
    cursor.execute("""
        SELECT position_id, side, qty, price, executed_at 
        FROM trades 
        WHERE position_id IN ('pos_f0c83651', 'pos_c955d000')
        ORDER BY executed_at DESC 
        LIMIT 5
    """)

    trades = cursor.fetchall()
    if trades:
        for pos_id, side, qty, price, executed_at in trades:
            print(f"  [{executed_at}] {pos_id}: {side} {qty:.4f} @ ${price:.2f}")
    else:
        print("  ⚠️  No trades found")

    conn.close()

    print("\n" + "=" * 80)
    print("\n💡 Next Steps:")
    print("  1. Fix portfolio state if not RUNNING")
    print("  2. Check for errors in trading service")
    print("  3. Run diagnostic: python scripts/diagnose_trading_issue.py pos_f0c83651")
    print("  4. Monitor: python scripts/monitor_trading.py pos_f0c83651 --duration 300")
    print("=" * 80)


if __name__ == "__main__":
    check_all()

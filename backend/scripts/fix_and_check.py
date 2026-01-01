#!/usr/bin/env python3
"""
Fix portfolio state and check trading status.
"""

import sys
import os
import sqlite3

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.di import container
from application.services.continuous_trading_service import get_continuous_trading_service


def main():
    print("=" * 80)
    print("FIXING PORTFOLIO STATE AND CHECKING TRADING")
    print("=" * 80)

    db_path = os.path.join(os.path.dirname(__file__), "..", "vb.sqlite")

    # Step 1: Check and fix portfolio state
    print("\n1️⃣  Checking Portfolio State...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, trading_state FROM portfolios")
    portfolios = cursor.fetchall()

    fixed = False
    for p_id, name, state in portfolios:
        if state != "RUNNING":
            print(f"   ❌ {name} ({p_id}): {state}")
            print("      → Fixing to RUNNING...")
            cursor.execute("UPDATE portfolios SET trading_state = 'RUNNING' WHERE id = ?", (p_id,))
            fixed = True
        else:
            print(f"   ✅ {name} ({p_id}): {state}")

    if fixed:
        conn.commit()
        print("\n   ✅ Portfolio state(s) fixed!")
    else:
        print("\n   ✅ All portfolios already in RUNNING state")

    conn.close()

    # Step 2: Check active positions
    print("\n2️⃣  Checking Active Positions for Trading...")
    try:
        # Check if we have the adapter (which has get_active_positions_for_trading)
        if hasattr(container, "live_trading_orchestrator") and hasattr(
            container.live_trading_orchestrator, "position_repo"
        ):
            position_repo = container.live_trading_orchestrator.position_repo
            if hasattr(position_repo, "get_active_positions_for_trading"):
                active_positions = list(position_repo.get_active_positions_for_trading())
                print(f"   Found {len(active_positions)} active position(s):")
                for pos_id in active_positions:
                    print(f"      ✅ {pos_id}")

                if len(active_positions) == 0:
                    print("\n   ⚠️  No active positions found!")
                    print("   This means:")
                    print("      - Portfolio state is not RUNNING, OR")
                    print("      - Positions don't have anchor_price set")
            else:
                print("   ⚠️  Position repo doesn't have get_active_positions_for_trading method")
        else:
            print("   ⚠️  Could not access position repo adapter")
    except Exception as e:
        print(f"   ⚠️  Error checking active positions: {e}")
        import traceback

        traceback.print_exc()

    # Step 3: Check continuous trading service
    print("\n3️⃣  Checking Continuous Trading Service...")
    service = get_continuous_trading_service()
    active = service.list_active()

    if not active:
        print("   ⚠️  No positions are actively trading")
        print(
            "   → Start trading: curl -X POST http://localhost:8000/v1/trading/start/<position_id>"
        )
    else:
        print(f"   Found {len(active)} position(s) in trading service:")
        for position_id, status in active.items():
            print(f"\n      Position: {position_id}")
            print(f"         Checks: {status.total_checks}")
            print(f"         Trades: {status.total_trades}")
            print(f"         Errors: {status.total_errors}")
            if status.last_error:
                print(f"         ⚠️  Last Error: {status.last_error}")
            if status.last_check:
                print(f"         Last Check: {status.last_check}")

    # Step 4: Check recent events
    print("\n4️⃣  Checking Recent Events...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check events table schema first
    cursor.execute("PRAGMA table_info(events)")
    columns = [row[1] for row in cursor.fetchall()]

    # Use appropriate timestamp column
    timestamp_col = (
        "ts" if "ts" in columns else ("created_at" if "created_at" in columns else "timestamp")
    )

    cursor.execute(f"""
        SELECT position_id, type, {timestamp_col} 
        FROM events 
        WHERE position_id IN ('pos_f0c83651', 'pos_c955d000')
        ORDER BY {timestamp_col} DESC 
        LIMIT 10
    """)

    events = cursor.fetchall()
    if events:
        print(f"   Found {len(events)} recent event(s):")
        for event in events[:5]:
            if len(event) >= 3:
                pos_id, event_type, timestamp = event[0], event[1], event[2]
                print(f"      [{timestamp}] {pos_id}: {event_type}")
            else:
                print(f"      {event}")
    else:
        print("   ⚠️  No recent events found")
        print("   → This suggests evaluation cycles aren't running")

    conn.close()

    print("\n" + "=" * 80)
    if fixed:
        print("\n✅ Portfolio state was fixed to RUNNING!")
        print("\n⚠️  IMPORTANT: You need to restart trading for positions to pick up the change:")
        print("   curl -X POST http://localhost:8000/v1/trading/stop/pos_f0c83651")
        print("   curl -X POST http://localhost:8000/v1/trading/start/pos_f0c83651")
        print("   curl -X POST http://localhost:8000/v1/trading/stop/pos_c955d000")
        print("   curl -X POST http://localhost:8000/v1/trading/start/pos_c955d000")
    print("\n💡 Next Steps:")
    print("   1. Monitor for activity:")
    print("      python scripts/monitor_trading.py pos_f0c83651 --duration 300")
    print("\n   2. Check diagnostic:")
    print("      python scripts/diagnose_trading_issue.py pos_f0c83651")
    print("\n   3. Check trading status:")
    print("      curl http://localhost:8000/v1/trading/status/pos_f0c83651")
    print("=" * 80)


if __name__ == "__main__":
    main()

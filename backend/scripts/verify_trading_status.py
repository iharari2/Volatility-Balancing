#!/usr/bin/env python3
"""
Verify trading status: Check if trades are executing and cash balances are updating.
"""

import os
import sys
import sqlite3
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

os.environ["APP_PERSISTENCE"] = "sql"
os.environ["SQL_URL"] = "sqlite:///vb.sqlite"


def verify_trading_status(position_id: str):
    """Verify trading status for a position."""
    db_path = backend_dir / "vb.sqlite"
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("=" * 80)
    print(f"VERIFYING TRADING STATUS FOR POSITION: {position_id}")
    print("=" * 80)

    # 1. Check position state
    print("\n1️⃣ POSITION STATE:")
    # Try asset_symbol first, fallback to ticker
    try:
        cursor.execute(
            "SELECT id, asset_symbol, qty, cash, anchor_price FROM positions WHERE id = ?",
            (position_id,),
        )
        pos = cursor.fetchone()
        if not pos:
            print(f"   ❌ Position {position_id} not found")
            return
        pos_id, symbol, qty, cash, anchor = pos
    except sqlite3.OperationalError:
        # Fallback to ticker if asset_symbol doesn't exist
        cursor.execute(
            "SELECT id, ticker, qty, cash, anchor_price FROM positions WHERE id = ?", (position_id,)
        )
        pos = cursor.fetchone()
        if not pos:
            print(f"   ❌ Position {position_id} not found")
            return
        pos_id, symbol, qty, cash, anchor = pos

    print(f"   ✅ Position found: {symbol}")
    print(f"   📊 Quantity: {qty:.4f}")
    print(f"   💵 Cash: ${cash:.2f}")
    print(f"   📍 Anchor: ${anchor:.2f}")

    # 2. Check timeline records
    print("\n2️⃣ TIMELINE RECORDS:")
    cursor.execute(
        """
        SELECT COUNT(*) FROM position_evaluation_timeline 
        WHERE position_id = ?
    """,
        (position_id,),
    )
    timeline_count = cursor.fetchone()[0]
    print(f"   📝 Total timeline records: {timeline_count}")

    if timeline_count > 0:
        # Try timestamp first, fallback to evaluated_at
        try:
            cursor.execute(
                """
                SELECT timestamp, action, action_taken, trigger_detected, 
                       position_qty_before, position_cash_before, market_price_raw
                FROM position_evaluation_timeline 
                WHERE position_id = ?
                ORDER BY timestamp DESC 
                LIMIT 5
            """,
                (position_id,),
            )
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            # Fallback to evaluated_at
            cursor.execute(
                """
                SELECT evaluated_at, action, action_taken, trigger_detected, 
                       position_qty_before, position_cash_before, market_price_raw
                FROM position_evaluation_timeline 
                WHERE position_id = ?
                ORDER BY evaluated_at DESC 
                LIMIT 5
            """,
                (position_id,),
            )
            rows = cursor.fetchall()

        print("   📋 Recent evaluations:")
        for row in rows:
            ts, action, action_taken, trigger_detected, qty_before, cash_before, price = row
            print(
                f"      • {ts}: action={action}, action_taken={action_taken}, trigger={trigger_detected}, price=${price:.2f}"
            )

    # 3. Check trades
    print("\n3️⃣ TRADES:")
    cursor.execute("SELECT COUNT(*) FROM trades WHERE position_id = ?", (position_id,))
    trade_count = cursor.fetchone()[0]
    print(f"   💼 Total trades: {trade_count}")

    if trade_count > 0:
        try:
            cursor.execute(
                """
                SELECT id, side, qty, price, commission, executed_at
                FROM trades 
                WHERE position_id = ?
                ORDER BY executed_at DESC 
                LIMIT 5
            """,
                (position_id,),
            )
            print("   📋 Recent trades:")
            for row in cursor.fetchall():
                trade_id, side, qty, price, commission, executed_at = row
                print(
                    f"      • {executed_at}: {side} {qty:.4f} @ ${price:.2f} (commission: ${commission:.2f})"
                )
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  Error querying trades: {e}")

    # 4. Check events
    print("\n4️⃣ EVENTS:")
    cursor.execute("SELECT COUNT(*) FROM events WHERE position_id = ?", (position_id,))
    event_count = cursor.fetchone()[0]
    print(f"   📨 Total events: {event_count}")

    if event_count > 0:
        try:
            cursor.execute(
                """
                SELECT type, message, ts
                FROM events 
                WHERE position_id = ?
                ORDER BY ts DESC 
                LIMIT 10
            """,
                (position_id,),
            )
            print("   📋 Recent events:")
            for row in cursor.fetchall():
                event_type, message, ts = row
                msg_preview = message[:60] + "..." if message and len(message) > 60 else message
                print(f"      • {ts}: {event_type} - {msg_preview}")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  Error querying events: {e}")

    # 5. Check orders
    print("\n5️⃣ ORDERS:")
    cursor.execute("SELECT COUNT(*) FROM orders WHERE position_id = ?", (position_id,))
    order_count = cursor.fetchone()[0]
    print(f"   📋 Total orders: {order_count}")

    if order_count > 0:
        try:
            cursor.execute(
                """
                SELECT id, side, qty, price, status, created_at
                FROM orders 
                WHERE position_id = ?
                ORDER BY created_at DESC 
                LIMIT 5
            """,
                (position_id,),
            )
            print("   📋 Recent orders:")
            for row in cursor.fetchall():
                order_id, side, qty, price, status, created_at = row
                print(f"      • {created_at}: {side} {qty:.4f} @ ${price:.2f} [{status}]")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  Error querying orders: {e}")

    # 6. Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"   Timeline records: {timeline_count}")
    print(f"   Trades executed: {trade_count}")
    print(f"   Events logged: {event_count}")
    print(f"   Orders created: {order_count}")

    if timeline_count > 0 and trade_count == 0:
        print("\n   ⚠️  WARNING: Timeline records exist but no trades executed!")
        print("   This suggests triggers may not be firing or orders are being rejected.")
    elif timeline_count > 0 and trade_count > 0:
        print("\n   ✅ GOOD: Both timeline records and trades exist!")

    conn.close()


if __name__ == "__main__":
    position_id = sys.argv[1] if len(sys.argv) > 1 else "pos_f0c83651"
    verify_trading_status(position_id)

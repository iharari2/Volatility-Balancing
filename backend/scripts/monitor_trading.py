#!/usr/bin/env python3
"""
Monitor trading activity to verify trades are executing.

Usage:
    python scripts/monitor_trading.py <position_id>
    python scripts/monitor_trading.py --all
"""

import sys
import os
import sqlite3
import time
import argparse

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.di import container
from application.services.continuous_trading_service import get_continuous_trading_service


def check_portfolio_state(portfolio_id):
    """Check if portfolio is in RUNNING state."""
    db_path = os.path.join(os.path.dirname(__file__), "..", "vb.sqlite")
    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT trading_state FROM portfolios WHERE id = ?", (portfolio_id,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def monitor_position(position_id, duration_seconds=60):
    """Monitor a position for trading activity."""
    print("=" * 80)
    print(f"MONITORING POSITION: {position_id}")
    print("=" * 80)

    # Get position info
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
    print(f"   Portfolio: {portfolio_id}")
    print(f"   Anchor Price: ${position.anchor_price:.2f}")
    print(f"   Current Qty: {position.qty}")
    print(f"   Current Cash: ${position.cash:.2f}")

    # Check portfolio state
    portfolio_state = check_portfolio_state(portfolio_id)
    if portfolio_state != "RUNNING":
        print(f"\n⚠️  WARNING: Portfolio state is '{portfolio_state}' (should be 'RUNNING')")
        print(f"   Run: python scripts/fix_portfolio_state.py --portfolio-id {portfolio_id}")
    else:
        print("\n✅ Portfolio state: RUNNING")

    # Check trading service status
    service = get_continuous_trading_service()
    status = service.get_status(position_id)

    if not status:
        print("\n❌ Continuous trading NOT running for this position")
        print(f"   Start it: curl -X POST http://localhost:8000/v1/trading/start/{position_id}")
        return

    print("\n✅ Continuous trading is running:")
    print(f"   Total Checks: {status.total_checks}")
    print(f"   Total Trades: {status.total_trades}")
    print(f"   Total Errors: {status.total_errors}")
    if status.last_error:
        print(f"   Last Error: {status.last_error}")
    if status.last_check:
        print(f"   Last Check: {status.last_check}")

    # Get initial state
    initial_cash = position.cash
    initial_qty = position.qty

    print("\n📊 Initial State:")
    print(f"   Cash: ${initial_cash:.2f}")
    print(f"   Qty: {initial_qty:.4f}")

    # Monitor for specified duration
    print(f"\n⏱️  Monitoring for {duration_seconds} seconds...")
    print("   (Press Ctrl+C to stop early)\n")

    start_time = time.time()
    check_interval = 10  # Check every 10 seconds

    try:
        while time.time() - start_time < duration_seconds:
            time.sleep(check_interval)

            # Reload position
            position = container.positions.get(tenant_id, portfolio_id, position_id)
            if not position:
                print("❌ Position not found during monitoring")
                break

            # Reload status
            status = service.get_status(position_id)

            elapsed = int(time.time() - start_time)
            print(
                f"[{elapsed}s] Checks: {status.total_checks}, Trades: {status.total_trades}, Errors: {status.total_errors}"
            )

            # Check for changes
            if position.cash != initial_cash:
                cash_change = position.cash - initial_cash
                print(
                    f"   💰 Cash changed: ${initial_cash:.2f} → ${position.cash:.2f} (${cash_change:+.2f})"
                )
                initial_cash = position.cash

            if position.qty != initial_qty:
                qty_change = position.qty - initial_qty
                print(
                    f"   📈 Qty changed: {initial_qty:.4f} → {position.qty:.4f} ({qty_change:+.4f})"
                )
                initial_qty = position.qty

            if status.total_trades > 0:
                print(f"   ✅ {status.total_trades} trade(s) executed!")

            if status.last_error:
                print(f"   ⚠️  Error: {status.last_error}")

    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")

    # Final state
    print("\n📊 Final State:")
    print(f"   Cash: ${position.cash:.2f} (change: ${position.cash - initial_cash:+.2f})")
    print(f"   Qty: {position.qty:.4f} (change: {position.qty - initial_qty:+.4f})")
    print(f"   Total Trades: {status.total_trades}")

    # Check recent events
    db_path = os.path.join(os.path.dirname(__file__), "..", "vb.sqlite")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get recent events
        cursor.execute(
            """
            SELECT type, created_at, message 
            FROM events 
            WHERE position_id = ? 
            ORDER BY created_at DESC 
            LIMIT 10
        """,
            (position_id,),
        )

        events = cursor.fetchall()
        if events:
            print(f"\n📋 Recent Events ({len(events)}):")
            for event_type, created_at, message in events[:5]:
                print(f"   [{created_at}] {event_type}: {message[:60]}")

        # Get recent trades
        cursor.execute(
            """
            SELECT side, qty, price, executed_at 
            FROM trades 
            WHERE position_id = ? 
            ORDER BY executed_at DESC 
            LIMIT 5
        """,
            (position_id,),
        )

        trades = cursor.fetchall()
        if trades:
            print(f"\n💼 Recent Trades ({len(trades)}):")
            for side, qty, price, executed_at in trades:
                print(f"   [{executed_at}] {side} {qty:.4f} @ ${price:.2f}")
        else:
            print("\n⚠️  No trades found in database")

        conn.close()

    print("\n" + "=" * 80)


def monitor_all():
    """Monitor all active trading positions."""
    service = get_continuous_trading_service()
    active = service.list_active()

    if not active:
        print("❌ No active trading positions found")
        print("   Start trading: curl -X POST http://localhost:8000/v1/trading/start/<position_id>")
        return

    print(f"Found {len(active)} active position(s):\n")

    for position_id, status in active.items():
        print(f"Position: {position_id}")
        print(
            f"  Checks: {status.total_checks}, Trades: {status.total_trades}, Errors: {status.total_errors}"
        )
        if status.last_error:
            print(f"  Last Error: {status.last_error}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Monitor trading activity")
    parser.add_argument("position_id", nargs="?", help="Position ID to monitor")
    parser.add_argument("--all", action="store_true", help="List all active positions")
    parser.add_argument(
        "--duration", type=int, default=60, help="Monitoring duration in seconds (default: 60)"
    )
    args = parser.parse_args()

    if args.all:
        monitor_all()
    elif args.position_id:
        monitor_position(args.position_id, args.duration)
    else:
        print("Usage:")
        print("  python scripts/monitor_trading.py <position_id>")
        print("  python scripts/monitor_trading.py --all")
        print("\nExample:")
        print("  python scripts/monitor_trading.py pos_f0c83651")


if __name__ == "__main__":
    main()

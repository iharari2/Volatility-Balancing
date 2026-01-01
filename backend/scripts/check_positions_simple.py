#!/usr/bin/env python3
"""
Simple script to check positions directly from SQLite database.
"""

import sys
import os
import sqlite3

# Database is at ./vb.sqlite relative to backend directory
db_path = os.path.join(os.path.dirname(__file__), "..", "vb.sqlite")

if not os.path.exists(db_path):
    print(f"❌ Database not found at: {db_path}")
    print("\nLooking for database files...")
    backend_dir = os.path.dirname(__file__)
    for file in os.listdir(backend_dir):
        if file.endswith(".sqlite"):
            print(f"  Found: {file}")
    sys.exit(1)

print(f"✅ Found database: {db_path}\n")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if positions table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='positions'")
    if not cursor.fetchone():
        print("❌ 'positions' table does not exist in database")
        print("\nAvailable tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for row in cursor.fetchall():
            print(f"  - {row[0]}")
        conn.close()
        sys.exit(1)

    # Get all positions
    cursor.execute("""
        SELECT 
            id, 
            tenant_id, 
            portfolio_id, 
            asset_symbol, 
            qty, 
            cash, 
            anchor_price,
            created_at
        FROM positions
        ORDER BY created_at DESC
    """)

    positions = cursor.fetchall()

    if not positions:
        print("❌ No positions found in database")
        print("\n💡 You may need to create positions first.")
        print("   Use the frontend or API to create positions with AAPL and ZIM.")
    else:
        print(f"✅ Found {len(positions)} position(s):\n")
        print("=" * 80)

        for pos in positions:
            pos_id, tenant_id, portfolio_id, asset_symbol, qty, cash, anchor_price, created_at = pos
            print(f"Position ID: {pos_id}")
            print(f"  Tenant: {tenant_id}")
            print(f"  Portfolio: {portfolio_id}")
            print(f"  Ticker: {asset_symbol}")
            print(f"  Quantity: {qty}")
            print(f"  Cash: ${cash:.2f}")
            if anchor_price:
                print(f"  Anchor Price: ${anchor_price:.2f} ✅")
            else:
                print("  Anchor Price: ❌ NOT SET - Trades won't execute!")
            print(f"  Created: {created_at}")
            print("-" * 80)
            print()

        # Show AAPL and ZIM specifically
        aapl_positions = [p for p in positions if p[3].upper() == "AAPL"]
        zim_positions = [p for p in positions if p[3].upper() == "ZIM"]

        if aapl_positions:
            print("\n📊 AAPL Positions:")
            for pos in aapl_positions:
                print(f"  - {pos[0]}: qty={pos[4]}, cash=${pos[5]:.2f}, anchor=${pos[6] or 0:.2f}")

        if zim_positions:
            print("\n📊 ZIM Positions:")
            for pos in zim_positions:
                print(f"  - {pos[0]}: qty={pos[4]}, cash=${pos[5]:.2f}, anchor=${pos[6] or 0:.2f}")

        print("\n" + "=" * 80)
        print("\nTo diagnose a position, run:")
        if positions:
            first_pos_id = positions[0][0]
            print(f"  python scripts/diagnose_trading_issue.py {first_pos_id}")
        print("=" * 80)

    # Check portfolios
    cursor.execute("SELECT id, tenant_id, name, trading_state FROM portfolios")
    portfolios = cursor.fetchall()

    if portfolios:
        print(f"\n📁 Found {len(portfolios)} portfolio(s):")
        for p_id, tenant_id, name, trading_state in portfolios:
            print(f"  - {name} ({p_id})")
            print(f"    Tenant: {tenant_id}, State: {trading_state}")

    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

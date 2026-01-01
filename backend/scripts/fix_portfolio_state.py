#!/usr/bin/env python3
"""
Fix portfolio trading state to RUNNING so trades can execute.

Usage:
    python scripts/fix_portfolio_state.py
    python scripts/fix_portfolio_state.py --portfolio-id pf_e009a8b4
"""

import sys
import os
import sqlite3
import argparse

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def fix_portfolio_state(portfolio_id=None):
    """Fix portfolio trading state to RUNNING."""
    db_path = os.path.join(os.path.dirname(__file__), "..", "vb.sqlite")

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if portfolio_id:
            # Fix specific portfolio
            cursor.execute(
                """
                SELECT id, name, trading_state 
                FROM portfolios 
                WHERE id = ?
            """,
                (portfolio_id,),
            )
            portfolio = cursor.fetchone()

            if not portfolio:
                print(f"❌ Portfolio {portfolio_id} not found")
                conn.close()
                return False

            p_id, name, current_state = portfolio
            print(f"Portfolio: {name} ({p_id})")
            print(f"  Current state: {current_state}")

            if current_state == "RUNNING":
                print("  ✅ Already in RUNNING state")
                conn.close()
                return True

            cursor.execute(
                """
                UPDATE portfolios 
                SET trading_state = 'RUNNING' 
                WHERE id = ?
            """,
                (portfolio_id,),
            )
            conn.commit()
            print("  ✅ Updated to RUNNING state")

        else:
            # Fix all portfolios
            cursor.execute("""
                SELECT id, name, trading_state 
                FROM portfolios
            """)
            portfolios = cursor.fetchall()

            if not portfolios:
                print("❌ No portfolios found")
                conn.close()
                return False

            print(f"Found {len(portfolios)} portfolio(s):\n")

            for p_id, name, current_state in portfolios:
                print(f"Portfolio: {name} ({p_id})")
                print(f"  Current state: {current_state}")

                if current_state == "RUNNING":
                    print("  ✅ Already in RUNNING state")
                else:
                    cursor.execute(
                        """
                        UPDATE portfolios 
                        SET trading_state = 'RUNNING' 
                        WHERE id = ?
                    """,
                        (p_id,),
                    )
                    print("  ✅ Updated to RUNNING state")

            conn.commit()

        conn.close()
        print("\n✅ Portfolio state(s) updated successfully!")
        print("\n💡 You may need to restart continuous trading for positions:")
        print("   - Stop: POST /v1/trading/stop/{position_id}")
        print("   - Start: POST /v1/trading/start/{position_id}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Fix portfolio trading state to RUNNING")
    parser.add_argument("--portfolio-id", type=str, help="Specific portfolio ID to fix")
    args = parser.parse_args()

    fix_portfolio_state(portfolio_id=args.portfolio_id)


if __name__ == "__main__":
    main()

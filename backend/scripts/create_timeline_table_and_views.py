# =========================
# backend/scripts/create_timeline_table_and_views.py
# =========================
"""
Migration script to create PositionEvaluationTimeline table and views.

This script:
1. Creates the PositionEvaluationTimeline table (if not exists)
2. Creates SQL views for different projections:
   - vw_eval_timeline_chronological: All rows, sorted by timestamp
   - vw_eval_timeline_per_position: Filtered by position_id, sorted by timestamp
   - vw_eval_timeline_action_only: Only rows where action != 'HOLD'
   - vw_eval_timeline_dividends: Only rows where dividend_applied = true
   - vw_eval_timeline_live: Only LIVE mode rows
   - vw_eval_timeline_simulation: Only SIMULATION mode rows
"""

from __future__ import annotations
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from infrastructure.persistence.sql.models import get_engine, create_all  # noqa: E402
from sqlalchemy import text  # noqa: E402


def create_views(engine):
    """Create SQL views for different projections of the timeline table."""
    views = [
        # Chronological view (default) - all rows sorted by timestamp
        """
        CREATE VIEW IF NOT EXISTS vw_eval_timeline_chronological AS
        SELECT *
        FROM position_evaluation_timeline
        ORDER BY timestamp ASC;
        """,
        # Per-position view - filtered by position_id, sorted by timestamp
        """
        CREATE VIEW IF NOT EXISTS vw_eval_timeline_per_position AS
        SELECT *
        FROM position_evaluation_timeline
        ORDER BY position_id, timestamp ASC;
        """,
        # Action-only view - only rows where action != 'HOLD'
        """
        CREATE VIEW IF NOT EXISTS vw_eval_timeline_action_only AS
        SELECT *
        FROM position_evaluation_timeline
        WHERE action IN ('BUY', 'SELL', 'SKIP')
        ORDER BY timestamp ASC;
        """,
        # Dividends view - only rows where dividend_applied = true
        """
        CREATE VIEW IF NOT EXISTS vw_eval_timeline_dividends AS
        SELECT *
        FROM position_evaluation_timeline
        WHERE dividend_applied = 1
        ORDER BY timestamp ASC;
        """,
        # Live trading view - only LIVE mode rows
        """
        CREATE VIEW IF NOT EXISTS vw_eval_timeline_live AS
        SELECT *
        FROM position_evaluation_timeline
        WHERE mode = 'LIVE'
        ORDER BY timestamp ASC;
        """,
        # Simulation view - only SIMULATION mode rows
        """
        CREATE VIEW IF NOT EXISTS vw_eval_timeline_simulation AS
        SELECT *
        FROM position_evaluation_timeline
        WHERE mode = 'SIMULATION'
        ORDER BY timestamp ASC;
        """,
        # Compact view (non-verbose columns only) - for Excel export Sheet 1
        """
        CREATE VIEW IF NOT EXISTS vw_eval_timeline_compact AS
        SELECT
            id, tenant_id, portfolio_id, portfolio_name, position_id, symbol,
            timestamp, mode, simulation_run_id, source,
            -- Market data (compact)
            effective_price, is_market_hours, allow_after_hours,
            -- Position state before
            position_qty_before, position_cash_before, position_stock_value_before,
            position_total_value_before, stock_pct,
            -- Strategy state
            anchor_price, pct_change_from_anchor,
            trigger_fired, trigger_direction, trigger_reason,
            guardrail_allowed, guardrail_block_reason,
            -- Action
            action, action_reason, trade_intent_qty, trade_intent_value,
            -- Execution (if any)
            order_id, trade_id, execution_price, execution_qty, execution_status,
            -- Position state after
            position_qty_after, position_cash_after, position_total_value_after,
            -- Portfolio impact
            portfolio_total_value_before, portfolio_total_value_after,
            position_weight_pct_before, position_weight_pct_after
        FROM position_evaluation_timeline
        ORDER BY timestamp ASC;
        """,
    ]

    with engine.connect() as conn:
        for view_sql in views:
            try:
                conn.execute(text(view_sql))
                conn.commit()
                print(f"✅ Created view: {view_sql.split('AS')[0].split()[-1]}")
            except Exception as e:
                print(f"⚠️  Error creating view: {e}")
                # Continue with other views


def main():
    """Main migration function."""
    import os

    sql_url = os.getenv("SQL_URL", "sqlite:///./vb.sqlite")
    print(f"Creating PositionEvaluationTimeline table and views in: {sql_url}")

    engine = get_engine(sql_url)

    # Create table (if not exists)
    print("Creating PositionEvaluationTimeline table...")
    create_all(engine)
    print("✅ Table created (or already exists)")

    # Create views
    print("\nCreating views...")
    create_views(engine)
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    main()

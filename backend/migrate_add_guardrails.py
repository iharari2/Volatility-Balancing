#!/usr/bin/env python3
"""Migration script to add guardrails columns to positions table"""

import os
import sys
from sqlalchemy import text

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infrastructure.persistence.sql.models import get_engine


def migrate_add_guardrails() -> None:
    """Add guardrails columns to the positions table"""
    engine = get_engine("sqlite:///./vb_test.sqlite")

    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(positions)"))
        columns = [row[1] for row in result.fetchall()]

        if "gr_min_stock_alloc_pct" not in columns:
            print("Adding guardrails columns to positions table...")
            conn.execute(
                text(
                    """
                ALTER TABLE positions 
                ADD COLUMN gr_min_stock_alloc_pct REAL
            """
                )
            )
            conn.execute(
                text(
                    """
                ALTER TABLE positions 
                ADD COLUMN gr_max_stock_alloc_pct REAL
            """
                )
            )
            conn.execute(
                text(
                    """
                ALTER TABLE positions 
                ADD COLUMN gr_max_orders_per_day INTEGER
            """
                )
            )
            conn.commit()
            print("Guardrails columns added successfully!")
        else:
            print("Guardrails columns already exist.")


if __name__ == "__main__":
    migrate_add_guardrails()

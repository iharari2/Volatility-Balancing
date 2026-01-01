#!/usr/bin/env python3
"""
Migration script to add commission and dividend tracking columns.

This script adds:
- positions.total_commission_paid
- positions.total_dividends_received
- orders.commission_rate_snapshot
- orders.commission_estimated
- trades.commission_rate_effective
- trades.status
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def column_exists(engine: Engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    if engine.url.drivername == "sqlite":
        # SQLite doesn't support information_schema, use pragma
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result]
                return column_name in columns
        except Exception as e:
            print(f"  Warning: Could not check column existence: {e}")
            return False
    else:
        # PostgreSQL/MySQL
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name AND column_name = :column_name
                    """
                ),
                {"table_name": table_name, "column_name": column_name},
            )
            return result.fetchone() is not None


def migrate(engine: Engine) -> None:
    """Run the migration."""
    print("Starting migration: Adding commission and dividend columns...")

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            # Add columns to positions table
            if not column_exists(engine, "positions", "total_commission_paid"):
                print("  Adding total_commission_paid to positions table...")
                conn.execute(
                    text(
                        "ALTER TABLE positions ADD COLUMN total_commission_paid REAL NOT NULL DEFAULT 0.0"
                    )
                )
            else:
                print("  Column total_commission_paid already exists in positions table")

            if not column_exists(engine, "positions", "total_dividends_received"):
                print("  Adding total_dividends_received to positions table...")
                conn.execute(
                    text(
                        "ALTER TABLE positions ADD COLUMN total_dividends_received REAL NOT NULL DEFAULT 0.0"
                    )
                )
            else:
                print("  Column total_dividends_received already exists in positions table")

            # Add columns to orders table
            if not column_exists(engine, "orders", "commission_rate_snapshot"):
                print("  Adding commission_rate_snapshot to orders table...")
                conn.execute(text("ALTER TABLE orders ADD COLUMN commission_rate_snapshot REAL"))
            else:
                print("  Column commission_rate_snapshot already exists in orders table")

            if not column_exists(engine, "orders", "commission_estimated"):
                print("  Adding commission_estimated to orders table...")
                conn.execute(text("ALTER TABLE orders ADD COLUMN commission_estimated REAL"))
            else:
                print("  Column commission_estimated already exists in orders table")

            # Add columns to trades table
            if not column_exists(engine, "trades", "commission_rate_effective"):
                print("  Adding commission_rate_effective to trades table...")
                conn.execute(text("ALTER TABLE trades ADD COLUMN commission_rate_effective REAL"))
            else:
                print("  Column commission_rate_effective already exists in trades table")

            if not column_exists(engine, "trades", "status"):
                print("  Adding status to trades table...")
                conn.execute(
                    text("ALTER TABLE trades ADD COLUMN status TEXT NOT NULL DEFAULT 'executed'")
                )
            else:
                print("  Column status already exists in trades table")

            # Commit transaction
            trans.commit()
            print("✅ Migration completed successfully!")

        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise


def main():
    """Main entry point."""
    sql_url = os.getenv("SQL_URL", "sqlite:///./vb.sqlite")

    if len(sys.argv) > 1:
        sql_url = sys.argv[1]

    print(f"Connecting to database: {sql_url}")
    engine = create_engine(sql_url)

    try:
        migrate(engine)
    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

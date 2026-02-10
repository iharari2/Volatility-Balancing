#!/usr/bin/env python3
"""
Migration script to add broker integration fields to orders table.

This script adds:
- orders.broker_order_id
- orders.broker_status
- orders.submitted_to_broker_at
- orders.filled_qty
- orders.avg_fill_price
- orders.total_commission
- orders.last_broker_update
- orders.rejection_reason

These fields support Phase 1 of broker integration.
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


def index_exists(engine: Engine, index_name: str) -> bool:
    """Check if an index exists."""
    if engine.url.drivername == "sqlite":
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name"),
                    {"name": index_name},
                )
                return result.fetchone() is not None
        except Exception as e:
            print(f"  Warning: Could not check index existence: {e}")
            return False
    else:
        # PostgreSQL
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE indexname = :index_name
                    """
                ),
                {"index_name": index_name},
            )
            return result.fetchone() is not None


def migrate(engine: Engine) -> None:
    """Run the migration."""
    print("Starting migration: Adding broker integration fields to orders...")

    columns_to_add = [
        ("broker_order_id", "TEXT"),
        ("broker_status", "TEXT"),
        ("submitted_to_broker_at", "TIMESTAMP"),
        ("filled_qty", "REAL DEFAULT 0.0"),
        ("avg_fill_price", "REAL"),
        ("total_commission", "REAL DEFAULT 0.0"),
        ("last_broker_update", "TIMESTAMP"),
        ("rejection_reason", "TEXT"),
    ]

    with engine.connect() as conn:
        trans = conn.begin()

        try:
            # Add columns
            for column_name, column_type in columns_to_add:
                if not column_exists(engine, "orders", column_name):
                    print(f"  Adding {column_name} to orders table...")
                    conn.execute(
                        text(f"ALTER TABLE orders ADD COLUMN {column_name} {column_type}")
                    )
                else:
                    print(f"  Column {column_name} already exists in orders table")

            # Add indexes for performance
            indexes = [
                ("ix_orders_broker_order_id", "broker_order_id"),
                ("ix_orders_broker_status", "broker_status"),
            ]

            for index_name, column_name in indexes:
                if not index_exists(engine, index_name):
                    print(f"  Creating index {index_name}...")
                    conn.execute(
                        text(f"CREATE INDEX {index_name} ON orders ({column_name})")
                    )
                else:
                    print(f"  Index {index_name} already exists")

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

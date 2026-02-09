#!/usr/bin/env python3
"""
Migration script to add time_in_force column to orders table.

This script adds:
- orders.time_in_force (TEXT DEFAULT 'day')

Supports the Order Control Loop feature — TIF-aware stale order handling.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def column_exists(engine: Engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    if engine.url.drivername == "sqlite":
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
    print("Starting migration: Adding time_in_force column to orders...")

    with engine.connect() as conn:
        trans = conn.begin()

        try:
            if not column_exists(engine, "orders", "time_in_force"):
                print("  Adding time_in_force to orders table...")
                conn.execute(
                    text("ALTER TABLE orders ADD COLUMN time_in_force TEXT DEFAULT 'day'")
                )
            else:
                print("  Column time_in_force already exists in orders table")

            trans.commit()
            print("Migration completed successfully!")

        except Exception as e:
            trans.rollback()
            print(f"Migration failed: {e}")
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

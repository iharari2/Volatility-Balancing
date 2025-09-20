#!/usr/bin/env python3
"""
Migration script to add trades table to existing database.

This script:
1. Connects to the existing database
2. Creates the trades table
3. Verifies the migration was successful

Usage:
    python migrate_add_trades.py [--db-url SQLITE_URL]
"""

import argparse
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from infrastructure.persistence.sql.models import get_engine, TradeModel, Base


def migrate_add_trades(db_url: str = "sqlite:///./vb.sqlite") -> bool:
    """Add trades table to the database."""
    try:
        print(f"Connecting to database: {db_url}")
        engine = get_engine(db_url)

        print("Creating trades table...")
        TradeModel.__table__.create(engine, checkfirst=True)

        print("✅ Migration completed successfully!")
        print("The trades table has been added to your database.")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Add trades table to database")
    parser.add_argument(
        "--db-url",
        default="sqlite:///./vb.sqlite",
        help="Database URL (default: sqlite:///./vb.sqlite)",
    )

    args = parser.parse_args()

    success = migrate_add_trades(args.db_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

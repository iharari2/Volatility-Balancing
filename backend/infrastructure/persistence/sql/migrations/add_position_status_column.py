#!/usr/bin/env python3
"""
Migration: Add status column to positions table

This migration adds the `status` column to the `positions` table if it doesn't exist.
The status column is used to track whether a position is RUNNING or PAUSED.

Usage:
    python -m backend.infrastructure.persistence.sql.migrations.add_position_status_column
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from app.di import get_db_url


def check_column_exists(connection, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(connection)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_status_column():
    """Add status column to positions table if it doesn't exist."""
    db_url = get_db_url()
    # For SQLite, use check_same_thread=False and ensure we can commit
    if "sqlite" in db_url.lower():
        engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(db_url, echo=False)

    with engine.begin() as conn:  # Use begin() for automatic transaction handling
        # Check if column already exists
        try:
            if check_column_exists(conn, "positions", "status"):
                print("[OK] Column 'status' already exists in 'positions' table")
                return
        except Exception as e:
            print(f"[WARNING] Could not check column existence: {e}")
            # Continue anyway - might be a new database

        # Determine database type
        is_sqlite = "sqlite" in db_url.lower()
        is_postgres = "postgresql" in db_url.lower() or "postgres" in db_url.lower()

        try:
            if is_sqlite:
                # SQLite syntax
                # First check if column exists by trying to query it
                try:
                    result = conn.execute(text("SELECT status FROM positions LIMIT 1"))
                    result.fetchone()  # Consume the result
                    print("[OK] Column 'status' already exists in 'positions' table")
                    return
                except Exception as check_error:
                    # Column doesn't exist, add it
                    if "no such column" not in str(check_error).lower():
                        # Some other error occurred
                        raise

                # SQLite doesn't support ALTER TABLE ADD COLUMN with DEFAULT in all versions
                # Use a workaround: add column, then update existing rows
                print("[INFO] Adding 'status' column to 'positions' table (SQLite)...")

                # SQLite requires the column to be added without NOT NULL first, then we can set defaults
                try:
                    conn.execute(
                        text(
                            """
                        ALTER TABLE positions 
                        ADD COLUMN status TEXT
                    """
                        )
                    )

                    # Update existing rows to have RUNNING status
                    conn.execute(
                        text(
                            """
                        UPDATE positions 
                        SET status = 'RUNNING' 
                        WHERE status IS NULL OR status = ''
                    """
                        )
                    )

                    # Now we can't add NOT NULL constraint in SQLite easily, but we've set defaults
                    # The application code should handle NULL as 'RUNNING'
                    print("[INFO] Set default 'RUNNING' status for existing rows")
                except Exception as alter_error:
                    if (
                        "duplicate column name" in str(alter_error).lower()
                        or "already exists" in str(alter_error).lower()
                    ):
                        print("[OK] Column 'status' already exists")
                        return
                    raise

                # Create index
                try:
                    conn.execute(
                        text(
                            """
                        CREATE INDEX IF NOT EXISTS ix_positions_status 
                        ON positions(status)
                    """
                        )
                    )
                except Exception as e:
                    print(f"[WARNING] Could not create index: {e}")

            elif is_postgres:
                # PostgreSQL syntax
                print("[INFO] Adding 'status' column to 'positions' table (PostgreSQL)...")
                conn.execute(
                    text(
                        """
                    ALTER TABLE positions 
                    ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'RUNNING'
                """
                    )
                )

                # Update existing rows
                conn.execute(
                    text(
                        """
                    UPDATE positions 
                    SET status = 'RUNNING' 
                    WHERE status IS NULL OR status = ''
                """
                    )
                )

                # Create index
                try:
                    conn.execute(
                        text(
                            """
                        CREATE INDEX IF NOT EXISTS ix_positions_status 
                        ON positions(status)
                    """
                        )
                    )
                except Exception as e:
                    print(f"[WARNING] Could not create index: {e}")

                # Add check constraint
                try:
                    conn.execute(
                        text(
                            """
                        ALTER TABLE positions 
                        ADD CONSTRAINT ck_positions_status 
                        CHECK (status IN ('RUNNING', 'PAUSED'))
                    """
                        )
                    )
                except Exception as e:
                    print(f"[WARNING] Could not add check constraint (may already exist): {e}")
            else:
                print(f"[ERROR] Unsupported database type: {db_url}")
                return

            # Transaction is automatically committed by 'with engine.begin()'
            print("[OK] Successfully added 'status' column to 'positions' table")

        except Exception as e:
            error_msg = str(e)
            if "database is locked" in error_msg.lower() or "locked" in error_msg.lower():
                print(
                    "[ERROR] Database is locked. Please stop the server before running the migration."
                )
                print(f"[ERROR] Error details: {e}")
                raise
            else:
                print(f"[ERROR] Migration failed: {e}")
                raise


if __name__ == "__main__":
    try:
        add_status_column()
        print("[OK] Migration completed successfully")
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        sys.exit(1)

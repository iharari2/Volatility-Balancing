#!/usr/bin/env python3
"""
Migration script to add anchor_price column to positions table.
"""

import sqlite3
from pathlib import Path

def migrate_add_anchor_price():
    """Add anchor_price column to positions table."""
    db_path = Path("vb.sqlite")
    
    if not db_path.exists():
        print("Database file not found. Creating new database...")
        return
    
    print(f"Migrating database: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if anchor_price column already exists
        cursor.execute("PRAGMA table_info(positions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'anchor_price' in columns:
            print("anchor_price column already exists. Skipping migration.")
            return
        
        # Add anchor_price column
        print("Adding anchor_price column to positions table...")
        cursor.execute("ALTER TABLE positions ADD COLUMN anchor_price REAL")
        
        # Commit the changes
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_anchor_price()

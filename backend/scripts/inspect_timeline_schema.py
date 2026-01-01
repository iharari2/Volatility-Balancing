#!/usr/bin/env python3
"""
Inspect the actual position_evaluation_timeline table schema.
This will help us understand what columns exist, their types, and constraints.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment
os.environ["APP_PERSISTENCE"] = "sql"
os.environ["SQL_URL"] = "sqlite:///vb.sqlite"


def inspect_schema():
    """Inspect the actual database schema."""
    db_path = backend_dir / "vb.sqlite"
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("=" * 80)
    print("POSITION_EVALUATION_TIMELINE TABLE SCHEMA INSPECTION")
    print("=" * 80)

    # Get table info
    cursor.execute("PRAGMA table_info(position_evaluation_timeline)")
    columns = cursor.fetchall()

    print(f"\n📊 Found {len(columns)} columns:\n")

    # Column info: (cid, name, type, notnull, default_value, pk)
    not_null_columns = []
    nullable_columns = []

    for col in columns:
        cid, name, col_type, notnull, default_val, pk = col
        is_not_null = notnull == 1
        is_pk = pk == 1

        status = "🔴 NOT NULL" if is_not_null else "🟢 NULLABLE"
        pk_marker = " (PRIMARY KEY)" if is_pk else ""
        default_marker = f" DEFAULT={default_val}" if default_val else ""

        print(f"{status} {name:40s} {col_type:20s}{default_marker}{pk_marker}")

        if is_not_null:
            not_null_columns.append(
                {"name": name, "type": col_type, "default": default_val, "is_pk": is_pk}
            )
        else:
            nullable_columns.append({"name": name, "type": col_type, "default": default_val})

    print("\n📋 Summary:")
    print(f"   Total columns: {len(columns)}")
    print(f"   NOT NULL columns: {len(not_null_columns)}")
    print(f"   NULLABLE columns: {len(nullable_columns)}")

    # Get CHECK constraints
    print("\n🔍 CHECK Constraints:")
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='table' AND name='position_evaluation_timeline'
    """)
    table_sql = cursor.fetchone()
    if table_sql:
        sql_text = table_sql[0]
        # Extract CHECK constraints
        import re

        check_constraints = re.findall(r"CHECK\s*\(([^)]+)\)", sql_text, re.IGNORECASE)
        for constraint in check_constraints:
            print(f"   {constraint}")

    # Get indexes
    print("\n📑 Indexes:")
    cursor.execute("""
        SELECT name, sql FROM sqlite_master 
        WHERE type='index' AND tbl_name='position_evaluation_timeline'
    """)
    indexes = cursor.fetchall()
    for idx_name, idx_sql in indexes:
        print(f"   {idx_name}")

    conn.close()

    # Generate Python dict for use in code
    print("\n📝 Python dict for required defaults:")
    print("required_defaults = {")
    for col in not_null_columns:
        if col["is_pk"]:
            continue
        col_name = col["name"]
        col_type = col["type"].upper()
        default_val = col["default"]

        # Determine Python default based on type
        if "INT" in col_type:
            py_default = "0" if not default_val else default_val
        elif "REAL" in col_type or "FLOAT" in col_type or "DOUBLE" in col_type:
            py_default = "0.0" if not default_val else default_val
        elif "TEXT" in col_type or "VARCHAR" in col_type or "STRING" in col_type:
            if col_name == "action" or col_name == "action_taken":
                py_default = '"HOLD"'
            elif col_name == "mode":
                py_default = '"LIVE"'
            elif col_name == "evaluation_type":
                py_default = '"DAILY_CHECK"'
            else:
                py_default = '""' if not default_val else f'"{default_val}"'
        elif "BOOLEAN" in col_type or "BOOL" in col_type:
            py_default = "False" if not default_val else ("True" if default_val == "1" else "False")
        elif "DATETIME" in col_type or "TIMESTAMP" in col_type:
            if col_name == "timestamp" or col_name == "evaluated_at":
                py_default = "datetime.now(timezone.utc)"
            else:
                py_default = "None"
        else:
            py_default = "None"

        print(f'    "{col_name}": {py_default},')
    print("}")

    return not_null_columns, nullable_columns


if __name__ == "__main__":
    inspect_schema()

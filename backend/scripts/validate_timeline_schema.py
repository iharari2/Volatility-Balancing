#!/usr/bin/env python3
"""
Validate position_evaluation_timeline schema and generate required defaults.
Run this to see all fields, their types, and generate the correct defaults.
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


def validate_schema():
    """Validate schema and generate required defaults."""
    # Try multiple possible database locations
    possible_paths = [
        backend_dir / "vb.sqlite",
        backend_dir / "scripts" / "vb.sqlite",
        backend_dir.parent / "vb.sqlite",
        Path("/home/iharari/Volatility-Balancing/backend/vb.sqlite"),
        Path("/home/iharari/Volatility-Balancing/backend/scripts/vb.sqlite"),
    ]

    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            print(f"✅ Found database: {db_path}")
            break

    if not db_path:
        print("❌ Database not found. Tried:")
        for path in possible_paths:
            exists = "✅" if path.exists() else "❌"
            print(f"   {exists} {path}")
        return None

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("=" * 80)
    print("POSITION_EVALUATION_TIMELINE SCHEMA VALIDATION")
    print("=" * 80)

    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='position_evaluation_timeline'
    """)
    table_exists = cursor.fetchone()

    if not table_exists:
        print("\n❌ Table 'position_evaluation_timeline' does not exist in database")
        print("   You may need to run migrations to create the table")
        conn.close()
        return None

    # Get table info
    cursor.execute("PRAGMA table_info(position_evaluation_timeline)")
    columns = cursor.fetchall()

    # Get CHECK constraints
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='table' AND name='position_evaluation_timeline'
    """)
    table_sql = cursor.fetchone()

    conn.close()

    # Parse columns: (cid, name, type, notnull, default_value, pk)
    schema = {}
    not_null_fields = []

    for col in columns:
        cid, name, col_type, notnull, default_val, pk = col
        is_not_null = notnull == 1
        is_pk = pk == 1

        schema[name] = {
            "type": col_type.upper(),
            "not_null": is_not_null,
            "default": default_val,
            "is_pk": is_pk,
        }

        if is_not_null and not is_pk:
            not_null_fields.append(name)

    print(f"\n📊 Found {len(columns)} total columns")
    print(f"🔴 {len(not_null_fields)} NOT NULL columns (excluding PK)\n")

    # Generate required defaults
    print("=" * 80)
    print("REQUIRED DEFAULTS FOR NOT NULL FIELDS")
    print("=" * 80)
    print("\nrequired_defaults = {")

    for field_name in sorted(not_null_fields):
        info = schema[field_name]
        col_type = info["type"]
        db_default = info["default"]

        # Determine Python default based on type and field name
        if "INT" in col_type:
            py_default = "0" if not db_default else db_default
        elif "REAL" in col_type or "FLOAT" in col_type or "DOUBLE" in col_type:
            py_default = "0.0" if not db_default else db_default
        elif "TEXT" in col_type or "VARCHAR" in col_type or "STRING" in col_type:
            if field_name in ["action", "action_taken"]:
                py_default = '"HOLD"'
            elif field_name == "mode":
                py_default = '"LIVE"'
            elif field_name == "evaluation_type":
                py_default = '"DAILY_CHECK"'
            elif field_name in ["tenant_id"]:
                py_default = '"default"'
            else:
                py_default = '""' if not db_default else f'"{db_default}"'
        elif "BOOLEAN" in col_type or "BOOL" in col_type:
            if db_default == "1" or db_default == "TRUE":
                py_default = "True"
            elif db_default == "0" or db_default == "FALSE":
                py_default = "False"
            else:
                py_default = "False"
        elif "DATETIME" in col_type or "TIMESTAMP" in col_type:
            if field_name in ["timestamp", "evaluated_at"]:
                py_default = "datetime.now(timezone.utc)"
            else:
                py_default = "None"
        else:
            py_default = "None"

        # Show what we're using
        source = f"(DB default: {db_default})" if db_default else "(inferred)"
        print(f'    "{field_name}": {py_default},  # {col_type} {source}')

    print("}")

    # Show CHECK constraints
    if table_sql:
        import re

        check_constraints = re.findall(r"CHECK\s*\(([^)]+)\)", table_sql[0], re.IGNORECASE)
        if check_constraints:
            print("\n🔍 CHECK Constraints:")
            for constraint in check_constraints:
                print(f"   {constraint}")

                # Extract action constraint values
                if "action" in constraint.lower():
                    valid_values = re.findall(r"'(\w+)'", constraint)
                    print(f"      → Valid action values: {valid_values}")

    # Generate field list for testing
    print("\n" + "=" * 80)
    print("FIELD LIST FOR TESTING")
    print("=" * 80)
    print(f"\nAll fields ({len(schema)}):")
    for field_name in sorted(schema.keys()):
        info = schema[field_name]
        status = "🔴 NOT NULL" if info["not_null"] else "🟢 NULLABLE"
        pk_marker = " (PK)" if info["is_pk"] else ""
        print(f"   {status} {field_name:40s} {info['type']:20s}{pk_marker}")

    return schema, not_null_fields


if __name__ == "__main__":
    validate_schema()

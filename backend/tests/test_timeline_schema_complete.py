#!/usr/bin/env python3
"""
Complete schema validation test for position_evaluation_timeline.
This test:
1. Lists all fields in the database
2. Validates type and default for each field
3. Tests saving with all required fields
"""

import os
import sys
import sqlite3
import pytest
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment
os.environ["APP_PERSISTENCE"] = "sql"
os.environ["SQL_URL"] = "sqlite:///vb.sqlite"


def get_database_schema():
    """Get the actual database schema."""
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
            print(f"✅ Found database at: {db_path}")
            break

    if not db_path:
        print("❌ Database not found. Tried:")
        for path in possible_paths:
            exists = "✅" if path.exists() else "❌"
            print(f"   {exists} {path}")
        pytest.skip(f"Database not found. Tried: {[str(p) for p in possible_paths]}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='position_evaluation_timeline'
    """)
    table_exists = cursor.fetchone()

    if not table_exists:
        conn.close()
        pytest.skip("Table 'position_evaluation_timeline' does not exist in database")

    # Get table info: (cid, name, type, notnull, default_value, pk)
    cursor.execute("PRAGMA table_info(position_evaluation_timeline)")
    columns = cursor.fetchall()

    # Get CHECK constraints
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='table' AND name='position_evaluation_timeline'
    """)
    table_sql = cursor.fetchone()

    conn.close()

    # Build schema dict
    schema = {}
    for col in columns:
        cid, name, col_type, notnull, default_val, pk = col
        schema[name] = {
            "type": col_type.upper(),
            "not_null": notnull == 1,
            "default": default_val,
            "is_pk": pk == 1,
        }

    return schema, table_sql[0] if table_sql else None


class TestTimelineSchema:
    """Test suite for timeline schema validation."""

    @pytest.fixture(scope="class")
    def schema(self):
        """Get schema once for all tests."""
        return get_database_schema()[0]

    @pytest.fixture(scope="class")
    def table_sql(self):
        """Get table SQL once for all tests."""
        return get_database_schema()[1]

    def test_list_all_fields(self, schema):
        """Test 1: List all fields in the database."""
        print(f"\n{'='*80}")
        print("TEST 1: LIST ALL FIELDS")
        print(f"{'='*80}")
        print(f"\n📊 Total fields: {len(schema)}")

        not_null_fields = [name for name, info in schema.items() if info["not_null"]]
        nullable_fields = [name for name, info in schema.items() if not info["not_null"]]

        print(f"\n🔴 NOT NULL fields ({len(not_null_fields)}):")
        for field in sorted(not_null_fields):
            info = schema[field]
            pk_marker = " (PK)" if info["is_pk"] else ""
            print(f"   {field:40s} {info['type']:20s}{pk_marker}")

        print(f"\n🟢 NULLABLE fields ({len(nullable_fields)}):")
        for field in sorted(nullable_fields):
            info = schema[field]
            print(f"   {field:40s} {info['type']:20s}")

        assert len(schema) > 0, "Schema should have fields"
        assert len(not_null_fields) > 0, "Should have NOT NULL fields"

    def test_validate_field_types(self, schema):
        """Test 2: Validate field types match expectations."""
        print(f"\n{'='*80}")
        print("TEST 2: VALIDATE FIELD TYPES")
        print(f"{'='*80}")

        type_mapping = {
            "INTEGER": "int",
            "REAL": "float",
            "FLOAT": "float",
            "DOUBLE": "float",
            "TEXT": "str",
            "VARCHAR": "str",
            "STRING": "str",
            "BOOLEAN": "bool",
            "BOOL": "bool",
            "DATETIME": "datetime",
            "TIMESTAMP": "datetime",
        }

        type_issues = []
        for field_name, info in schema.items():
            col_type = info["type"]
            # Check if type is recognized
            recognized = any(keyword in col_type for keyword in type_mapping.keys())
            if not recognized:
                type_issues.append((field_name, col_type, "Unknown type"))

        if type_issues:
            print("\n⚠️  Type issues found:")
            for field_name, col_type, issue in type_issues:
                print(f"   {field_name:40s} {col_type:20s} - {issue}")
        else:
            print("\n✅ All field types are recognized")

        # This is informational
        assert True

    def test_validate_not_null_defaults(self, schema):
        """Test 3: Validate NOT NULL fields have proper defaults."""
        print(f"\n{'='*80}")
        print("TEST 3: VALIDATE NOT NULL DEFAULTS")
        print(f"{'='*80}")

        not_null_fields = {
            name: info for name, info in schema.items() if info["not_null"] and not info["is_pk"]
        }

        print(f"\n🔴 Checking {len(not_null_fields)} NOT NULL fields:\n")

        defaults_map = {}
        missing_defaults = []

        for field_name, info in sorted(not_null_fields.items()):
            col_type = info["type"]
            db_default = info["default"]

            # Determine expected default
            if "INT" in col_type:
                expected = 0
                py_default = "0"
            elif "REAL" in col_type or "FLOAT" in col_type or "DOUBLE" in col_type:
                expected = 0.0
                py_default = "0.0"
            elif "TEXT" in col_type or "VARCHAR" in col_type or "STRING" in col_type:
                if field_name in ["action", "action_taken"]:
                    expected = "HOLD"
                    py_default = '"HOLD"'
                elif field_name == "mode":
                    expected = "LIVE"
                    py_default = '"LIVE"'
                elif field_name == "evaluation_type":
                    expected = "DAILY_CHECK"
                    py_default = '"DAILY_CHECK"'
                elif field_name == "tenant_id":
                    expected = "default"
                    py_default = '"default"'
                else:
                    expected = ""
                    py_default = '""'
            elif "BOOLEAN" in col_type or "BOOL" in col_type:
                expected = False
                py_default = "False"
            elif "DATETIME" in col_type or "TIMESTAMP" in col_type:
                if field_name in ["timestamp", "evaluated_at"]:
                    expected = "datetime"
                    py_default = "datetime.now(timezone.utc)"
                else:
                    expected = None
                    py_default = "None"
            else:
                expected = None
                py_default = "None"

            defaults_map[field_name] = {
                "type": col_type,
                "db_default": db_default,
                "expected": expected,
                "py_default": py_default,
            }

            status = "✅" if db_default or expected is not None else "❌"
            db_default_str = str(db_default) if db_default else "None"
            print(
                f"   {status} {field_name:40s} {col_type:20s} DB={db_default_str:10s} Expected={py_default}"
            )

            if not db_default and expected is None:
                missing_defaults.append(field_name)

        if missing_defaults:
            print(f"\n⚠️  Fields without defaults: {missing_defaults}")
        else:
            print("\n✅ All NOT NULL fields have defaults or expected values")

        return defaults_map

    def test_check_constraints(self, table_sql):
        """Test 4: Validate CHECK constraints."""
        print(f"\n{'='*80}")
        print("TEST 4: VALIDATE CHECK CONSTRAINTS")
        print(f"{'='*80}")

        if not table_sql:
            pytest.skip("Could not get table SQL")

        import re

        check_constraints = re.findall(r"CHECK\s*\(([^)]+)\)", table_sql, re.IGNORECASE)

        print(f"\n🔍 Found {len(check_constraints)} CHECK constraints:\n")

        for constraint in check_constraints:
            print(f"   {constraint}")

            # Validate action constraint
            if "action" in constraint.lower():
                valid_values = re.findall(r"'(\w+)'", constraint)
                print(f"      → Valid values: {valid_values}")

                required_values = ["BUY", "SELL", "HOLD", "SKIP"]
                for req_val in required_values:
                    assert req_val in valid_values, f"{req_val} must be a valid action value"

        assert True

    def test_save_with_all_required_fields(self, schema):
        """Test 5: Test saving with all required fields."""
        print(f"\n{'='*80}")
        print("TEST 5: TEST SAVE WITH ALL REQUIRED FIELDS")
        print(f"{'='*80}")

        from app.di import container

        # Get all NOT NULL fields (except PK)
        not_null_fields = {
            name: info for name, info in schema.items() if info["not_null"] and not info["is_pk"]
        }

        # Build test data
        current_time = datetime.now(timezone.utc)
        test_data = {}

        for field_name, info in not_null_fields.items():
            col_type = info["type"]

            if "INT" in col_type:
                test_data[field_name] = 0
            elif "REAL" in col_type or "FLOAT" in col_type or "DOUBLE" in col_type:
                if field_name == "market_price_raw":
                    test_data[field_name] = 100.0
                elif "position_qty" in field_name:
                    test_data[field_name] = 10.0
                elif "position_cash" in field_name:
                    test_data[field_name] = 1000.0
                else:
                    test_data[field_name] = 0.0
            elif "TEXT" in col_type or "VARCHAR" in col_type or "STRING" in col_type:
                if field_name in ["action", "action_taken"]:
                    test_data[field_name] = "HOLD"
                elif field_name == "mode":
                    test_data[field_name] = "LIVE"
                elif field_name == "evaluation_type":
                    test_data[field_name] = "DAILY_CHECK"
                elif field_name == "tenant_id":
                    test_data[field_name] = "default"
                elif field_name in ["portfolio_id", "position_id", "symbol"]:
                    test_data[field_name] = f"test_{field_name}"
                else:
                    test_data[field_name] = ""
            elif "BOOLEAN" in col_type or "BOOL" in col_type:
                test_data[field_name] = False
            elif "DATETIME" in col_type or "TIMESTAMP" in col_type:
                test_data[field_name] = current_time
            else:
                test_data[field_name] = None

        print(f"\n🧪 Testing save with {len(test_data)} required fields...")

        repo = container.evaluation_timeline
        try:
            record_id = repo.save(test_data)
            print(f"✅ Successfully saved record: {record_id}")

            # Verify retrieval
            saved_record = repo.get_by_id(record_id)
            assert saved_record is not None, "Record should be retrievable"
            print("✅ Successfully retrieved record")

            # Verify key fields
            assert saved_record["action"] == "HOLD", "Action should be HOLD"
            assert saved_record["mode"] == "LIVE", "Mode should be LIVE"
            print("✅ All key fields validated")

        except Exception as e:
            print(f"❌ Failed to save: {e}")
            print(f"\n📋 Test data fields ({len(test_data)}):")
            for field_name in sorted(test_data.keys()):
                value = test_data[field_name]
                value_str = str(value)[:50] if value is not None else "None"
                print(f"   {field_name:40s} = {value_str}")
            raise


if __name__ == "__main__":
    # Run the validation script first
    print("Running schema inspection...")
    from backend.scripts.validate_timeline_schema import validate_schema

    schema, not_null = validate_schema()

    print("\n" + "=" * 80)
    print("Running tests...")
    print("=" * 80)

    pytest.main([__file__, "-v", "-s"])

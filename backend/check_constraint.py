#!/usr/bin/env python3
"""Check the actual constraint definition in the database."""

from sqlalchemy import create_engine, text
import os
import re

# Find the database file
db_path = os.path.join(os.path.dirname(__file__), "..", "data", "trading.db")
if not os.path.exists(db_path):
    db_path = os.path.join(os.path.dirname(__file__), "data", "trading.db")
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

print(f"Checking database at: {db_path}")
engine = create_engine(f"sqlite:///{db_path}")

with engine.connect() as conn:
    result = conn.execute(
        text(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='position_evaluation_timeline'"
        )
    ).scalar()
    if result:
        print("\n=== Full table definition (first 3000 chars) ===")
        print(result[:3000])
        print("\n=== Searching for ck_eval_timeline_action constraint ===")

        # Find the constraint
        match = re.search(
            r"ck_eval_timeline_action[^,)]*\(([^)]+)\)", result, re.IGNORECASE | re.DOTALL
        )
        if match:
            print(f"Constraint definition found: {match.group(1)}")
            values = [v.strip().strip("'\"") for v in match.group(1).split(",")]
            print(f"Constraint allows values: {values}")
        else:
            print(
                "Could not find constraint with pattern ck_eval_timeline_action[^,)]*\\(([^)]+)\\)"
            )

        # Also check for action IN or action_taken IN
        action_match = re.search(r"action\s+IN\s*\(([^)]+)\)", result, re.IGNORECASE | re.DOTALL)
        if action_match:
            print(f"\naction IN values: {action_match.group(1)}")
            values = [v.strip().strip("'\"") for v in action_match.group(1).split(",")]
            print(f"action allows: {values}")

        action_taken_match = re.search(
            r"action_taken\s+IN\s*\(([^)]+)\)", result, re.IGNORECASE | re.DOTALL
        )
        if action_taken_match:
            print(f"\naction_taken IN values: {action_taken_match.group(1)}")
            values = [v.strip().strip("'\"") for v in action_taken_match.group(1).split(",")]
            print(f"action_taken allows: {values}")

        # Find all CHECK constraints
        print("\n=== All CHECK constraints ===")
        check_constraints = re.findall(
            r"CheckConstraint\([^)]+\)", result, re.IGNORECASE | re.DOTALL
        )
        for constraint in check_constraints:
            if "action" in constraint.lower():
                print(f"Found: {constraint[:200]}...")
    else:
        print("Table not found")

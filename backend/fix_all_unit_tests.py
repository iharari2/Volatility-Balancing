#!/usr/bin/env python3
"""
Comprehensive Unit Test Fix Script
Fixes all portfolio-scoped migration issues in unit tests
"""

import re
from pathlib import Path


def fix_file(file_path: Path):
    """Fix a single test file"""
    print(f"Fixing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Fix 1: Position creation - ticker -> asset_symbol, remove cash
    # Pattern: Position(..., ticker="...", ..., cash=...)
    pattern1 = r'Position\s*\(\s*([^)]*ticker\s*=\s*["\']([^"\']+)["\'])([^)]*)(cash\s*=\s*[^,)]+)([^)]*)\)'

    def replace_position1(match):
        before = match.group(1)
        match.group(2)
        middle = match.group(3)
        cash_part = match.group(4)
        after = match.group(5)

        # Replace ticker= with asset_symbol=
        new_before = before.replace("ticker=", "asset_symbol=")
        # Remove cash= part
        new_middle = middle
        new_after = after.replace(cash_part, "").strip()
        if new_after.startswith(","):
            new_after = new_after[1:].strip()
        if new_after.endswith(","):
            new_after = new_after[:-1].strip()

        # Check if tenant_id and portfolio_id are present
        full_match = match.group(0)
        if "tenant_id=" not in full_match:
            new_before = f'tenant_id="default", portfolio_id="test_portfolio", {new_before}'

        return f"Position({new_before}{new_middle}{new_after})"

    # Fix 2: Simple ticker= in Position creation
    pattern2 = r'Position\s*\(\s*([^,)]+),\s*ticker\s*=\s*["\']([^"\']+)["\']'

    def replace_position2(match):
        before = match.group(1)
        ticker_value = match.group(2)
        # Check if already has tenant_id
        if "tenant_id=" not in before:
            return f'Position(tenant_id="default", portfolio_id="test_portfolio", {before}, asset_symbol="{ticker_value}"'
        return f'Position({before}, asset_symbol="{ticker_value}"'

    # Fix 3: process_ex_dividend_date calls
    pattern3 = r"process_ex_dividend_date\s*\(\s*([^,)]+)\s*\)"

    def replace_ex_dividend(match):
        pos_id = match.group(1).strip()
        if "tenant_id=" not in pos_id:
            return f'process_ex_dividend_date(tenant_id="default", portfolio_id="test_portfolio", position_id={pos_id})'
        return match.group(0)

    # Fix 4: process_dividend_payment calls (2 params)
    pattern4 = r"process_dividend_payment\s*\(\s*([^,)]+),\s*([^)]+)\s*\)"

    def replace_dividend_payment(match):
        param1 = match.group(1).strip()
        param2 = match.group(2).strip()
        if "tenant_id=" not in param1:
            return f'process_dividend_payment(tenant_id="default", portfolio_id="test_portfolio", position_id={param1}, receivable_id={param2})'
        return match.group(0)

    # Fix 5: get_dividend_status calls
    pattern5 = r"get_dividend_status\s*\(\s*([^)]+)\s*\)"

    def replace_dividend_status(match):
        param = match.group(1).strip()
        if "tenant_id=" not in param:
            return f'get_dividend_status(tenant_id="default", portfolio_id="test_portfolio", position_id={param})'
        return match.group(0)

    # Apply fixes
    content = re.sub(pattern1, replace_position1, content)
    content = re.sub(pattern2, replace_position2, content)
    content = re.sub(pattern3, replace_ex_dividend, content)
    content = re.sub(pattern4, replace_dividend_payment, content)
    content = re.sub(pattern5, replace_dividend_status, content)

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Fixed {file_path.name}")
        return True
    else:
        print(f"  - No changes needed for {file_path.name}")
        return False


def main():
    """Main function to fix all unit tests"""
    backend_dir = Path(__file__).parent
    tests_dir = backend_dir / "tests" / "unit"

    print("=" * 80)
    print("Fixing All Unit Tests")
    print("=" * 80)
    print()

    fixed_count = 0
    total_count = 0

    # Find all Python test files
    for test_file in tests_dir.rglob("test_*.py"):
        total_count += 1
        if fix_file(test_file):
            fixed_count += 1

    print()
    print("=" * 80)
    print(f"Summary: Fixed {fixed_count} out of {total_count} files")
    print("=" * 80)


if __name__ == "__main__":
    main()

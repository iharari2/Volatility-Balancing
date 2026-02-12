#!/usr/bin/env python3
"""
Test Failure Analysis Script
Analyzes pytest output to categorize errors and failures
"""

import subprocess
import re
from collections import defaultdict
from pathlib import Path


def run_tests():
    """Run tests and capture output"""
    print("Running tests...")
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )
    return result.stdout + result.stderr


def analyze_errors(output):
    """Analyze errors from test output"""
    errors = []
    error_pattern = re.compile(r"^([^:]+)::([^:]+)::([^\s]+)\s+ERROR")

    for line in output.split("\n"):
        if "ERROR" in line and "::" in line:
            match = error_pattern.match(line.strip())
            if match:
                file_path, class_name, test_name = match.groups()
                errors.append(
                    {"file": file_path, "class": class_name, "test": test_name, "line": line}
                )

    return errors


def analyze_failures(output):
    """Analyze failures from test output"""
    failures = []
    failure_pattern = re.compile(r"^([^:]+)::([^:]+)::([^\s]+)\s+FAILED")

    for line in output.split("\n"):
        if "FAILED" in line and "::" in line:
            match = failure_pattern.match(line.strip())
            if match:
                file_path, class_name, test_name = match.groups()
                failures.append(
                    {"file": file_path, "class": class_name, "test": test_name, "line": line}
                )

    return failures


def extract_error_details(output):
    """Extract detailed error information"""
    error_details = []
    lines = output.split("\n")

    i = 0
    while i < len(lines):
        if "ERROR" in lines[i] and "::" in lines[i]:
            error_block = []
            # Capture error context (5 lines before, 15 lines after)
            start = max(0, i - 5)
            end = min(len(lines), i + 15)
            error_block = lines[start:end]
            error_details.append("\n".join(error_block))
        i += 1

    return error_details


def categorize_errors(errors, output):
    """Categorize errors by type"""
    categories = defaultdict(list)

    for error in errors:
        # Try to find error message in output
        error["file"]
        error["test"]

        # Look for common error patterns
        if "ImportError" in output or "ModuleNotFoundError" in output:
            categories["Import Errors"].append(error)
        elif "TypeError" in output:
            categories["Type Errors"].append(error)
        elif "AttributeError" in output:
            categories["Attribute Errors"].append(error)
        elif "KeyError" in output:
            categories["Key Errors"].append(error)
        elif "ValueError" in output:
            categories["Value Errors"].append(error)
        else:
            categories["Other Errors"].append(error)

    return categories


def count_by_file(items):
    """Count items by file"""
    file_counts = defaultdict(int)
    for item in items:
        file_counts[item["file"]] += 1
    return dict(sorted(file_counts.items(), key=lambda x: x[1], reverse=True))


def main():
    """Main analysis function"""
    print("=" * 80)
    print("Test Failure Analysis")
    print("=" * 80)
    print()

    # Run tests
    output = run_tests()

    # Analyze errors
    print("Analyzing errors...")
    errors = analyze_errors(output)
    print(f"Found {len(errors)} errors")

    # Analyze failures
    print("Analyzing failures...")
    failures = analyze_failures(output)
    print(f"Found {len(failures)} failures")

    # Count by file
    print("\n" + "=" * 80)
    print("ERRORS BY FILE (Top 10)")
    print("=" * 80)
    error_counts = count_by_file(errors)
    for file, count in list(error_counts.items())[:10]:
        print(f"  {count:3d}  {file}")

    print("\n" + "=" * 80)
    print("FAILURES BY FILE (Top 10)")
    print("=" * 80)
    failure_counts = count_by_file(failures)
    for file, count in list(failure_counts.items())[:10]:
        print(f"  {count:3d}  {file}")

    # Extract error details
    print("\n" + "=" * 80)
    print("ERROR DETAILS (First 5)")
    print("=" * 80)
    error_details = extract_error_details(output)
    for i, detail in enumerate(error_details[:5], 1):
        print(f"\n--- Error {i} ---")
        print(detail[:500])  # First 500 chars
        if len(detail) > 500:
            print("...")

    # Save detailed report
    report_file = Path(__file__).parent / "test_analysis_report.txt"
    with open(report_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("TEST ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Errors: {len(errors)}\n")
        f.write(f"Total Failures: {len(failures)}\n\n")

        f.write("ERRORS BY FILE\n")
        f.write("-" * 80 + "\n")
        for file, count in error_counts.items():
            f.write(f"{count:3d}  {file}\n")

        f.write("\nFAILURES BY FILE\n")
        f.write("-" * 80 + "\n")
        for file, count in failure_counts.items():
            f.write(f"{count:3d}  {file}\n")

        f.write("\n\nERROR DETAILS\n")
        f.write("-" * 80 + "\n")
        for i, detail in enumerate(error_details, 1):
            f.write(f"\n--- Error {i} ---\n")
            f.write(detail + "\n")

    print(f"\n✓ Detailed report saved to: {report_file}")

    # List all error files
    print("\n" + "=" * 80)
    print("ALL ERROR FILES")
    print("=" * 80)
    for file in error_counts.keys():
        print(f"  {file}")

    return errors, failures, error_counts, failure_counts


if __name__ == "__main__":
    errors, failures, error_counts, failure_counts = main()

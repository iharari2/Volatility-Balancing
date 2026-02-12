#!/usr/bin/env python3
"""
QA Test Execution Script
Runs comprehensive test suite and generates detailed reports
"""

import subprocess
import os
from datetime import datetime
from pathlib import Path


def run_command(cmd, capture_output=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture_output, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def main():
    """Main test execution function"""
    print("=" * 80)
    print("QA Test Execution - Volatility Balancing System")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    # Test 1: Collect all tests
    print("Step 1: Collecting tests...")
    returncode, stdout, stderr = run_command("python -m pytest tests/ --collect-only -q")
    if returncode == 0:
        stdout.count("test session starts")
        print("✓ Found tests (checking collection)")
    else:
        print("✗ Test collection failed")
        print(stderr)

    # Test 2: Run unit tests
    print("\nStep 2: Running unit tests...")
    returncode, stdout, stderr = run_command("python -m pytest tests/unit/ -v --tb=short")
    unit_output = stdout + stderr
    print(f"Unit tests completed with exit code: {returncode}")

    # Test 3: Run integration tests
    print("\nStep 3: Running integration tests...")
    returncode, stdout, stderr = run_command("python -m pytest tests/integration/ -v --tb=short")
    integration_output = stdout + stderr
    print(f"Integration tests completed with exit code: {returncode}")

    # Test 4: Run regression tests
    print("\nStep 4: Running regression tests...")
    returncode, stdout, stderr = run_command("python -m pytest tests/regression/ -v --tb=short")
    regression_output = stdout + stderr
    print(f"Regression tests completed with exit code: {returncode}")

    # Test 5: Generate coverage report
    print("\nStep 5: Generating coverage report...")
    returncode, stdout, stderr = run_command(
        "python -m pytest tests/ --cov=backend --cov-report=term --cov-report=html -q"
    )
    coverage_output = stdout + stderr
    print(f"Coverage report generated with exit code: {returncode}")

    # Save detailed report
    report_file = backend_dir / f"qa_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("QA Test Execution Report\n")
        f.write("=" * 80 + "\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n\n")
        f.write("UNIT TESTS\n")
        f.write("-" * 80 + "\n")
        f.write(unit_output)
        f.write("\n\nINTEGRATION TESTS\n")
        f.write("-" * 80 + "\n")
        f.write(integration_output)
        f.write("\n\nREGRESSION TESTS\n")
        f.write("-" * 80 + "\n")
        f.write(regression_output)
        f.write("\n\nCOVERAGE REPORT\n")
        f.write("-" * 80 + "\n")
        f.write(coverage_output)

    print(f"\n✓ Detailed report saved to: {report_file}")
    print("\n" + "=" * 80)
    print("Test execution complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

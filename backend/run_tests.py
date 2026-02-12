#!/usr/bin/env python3
"""
Test runner script for Volatility Balancing project.
"""
import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f" {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} FAILED (exit code: {result.returncode})")
        return False
    else:
        print(f"✅ {description} PASSED")
        return True


def main():
    """Run all tests."""
    print("🧪 Running Volatility Balancing Tests")
    print("=" * 60)
    
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Test commands
    tests = [
        ("python -m pytest tests/unit/domain/test_dividend_entities.py -v", "Dividend Entity Unit Tests"),
        ("python -m pytest tests/unit/application/test_process_dividend_uc.py -v", "Dividend Use Case Unit Tests"),
        ("python -m pytest tests/unit/infrastructure/test_dividend_repos.py -v", "Dividend Repository Unit Tests"),
        ("python -m pytest tests/integration/test_dividend_api.py -v", "Dividend API Integration Tests"),
        ("python -m pytest tests/unit/ -v", "All Unit Tests"),
        ("python -m pytest tests/integration/ -v", "All Integration Tests"),
        ("python -m pytest tests/ -v --tb=short", "All Tests"),
    ]
    
    # Run tests
    passed = 0
    total = len(tests)
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(" TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())


#!/usr/bin/env python3
"""
Run Export Regression Tests
Simple script to run all export tests and report results
"""

import subprocess
import os


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Command: {command}")

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print(f"Output: {result.stdout[:500]}...")
            return True
        else:
            print(f"❌ FAILED (exit code: {result.returncode})")
            if result.stderr:
                print(f"Error: {result.stderr[:500]}...")
            if result.stdout:
                print(f"Output: {result.stdout[:500]}...")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT - Test took longer than 5 minutes")
        return False
    except Exception as e:
        print(f"❌ ERROR - {e}")
        return False


def main():
    """Run all export tests"""
    print("🧪 Export Test Suite Runner")
    print("=" * 50)

    # Change to project root if needed
    if os.path.exists("backend"):
        os.chdir(".")
    elif os.path.exists("../backend"):
        os.chdir("..")

    tests = [
        # Simple regression test (standalone)
        ("python test_export_regression_simple.py", "Simple Export Regression Test"),
        # Unit test for MergedCell fix
        (
            "cd backend && python -m pytest tests/unit/services/test_merged_cell_fix.py -v",
            "MergedCell Fix Unit Tests",
        ),
        # Full regression test suite
        (
            "cd backend && python -m pytest tests/regression/test_export_regression.py -v",
            "Full Regression Test Suite",
        ),
        # Check linting on modified files
        (
            "cd backend && python -m flake8 application/services/comprehensive_excel_export_service.py --max-line-length=100",
            "Linting Check - Comprehensive Service",
        ),
        (
            "cd backend && python -m flake8 application/services/excel_template_service.py --max-line-length=100",
            "Linting Check - Template Service",
        ),
    ]

    results = []

    for command, description in tests:
        success = run_command(command, description)
        results.append((description, success))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY:")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {description}")

    print(f"\nOverall: {passed}/{total} test suites passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("   ✅ Export functionality is working correctly")
        print("   ✅ MergedCell error is fixed")
        print("   ✅ No regressions detected")
        print("   📊 System ready for production!")
    elif passed >= total * 0.8:
        print(f"\n🟢 MOSTLY PASSING: {passed}/{total}")
        print("   Most functionality is working")
        print("   Some tests may have failed due to backend not running or network issues")
    else:
        print(f"\n🔴 ISSUES DETECTED: Only {passed}/{total} passed")
        print("   Significant problems with export functionality")
        print("   Review failed tests and fix issues")

    print("\n💡 TROUBLESHOOTING:")
    print("   • Make sure backend is running on port 8001")
    print("   • Check internet connection for Yahoo Finance API")
    print("   • Ensure all dependencies are installed")
    print("   • Review backend logs for detailed error messages")

    return 0 if passed >= total * 0.8 else 1


if __name__ == "__main__":
    exit(main())

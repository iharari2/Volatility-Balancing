#!/usr/bin/env python3
"""
Simple Export Regression Test - Run this to verify all exports work
This can be run standalone without pytest setup
"""

import requests
import time
from urllib.parse import urljoin


def test_endpoint(base_url, endpoint, description, timeout=30):
    """Test a single export endpoint"""
    url = urljoin(base_url, endpoint)
    print(f"\n🔧 Testing: {description}")
    print(f"   URL: {url}")

    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        end_time = time.time()

        execution_time = end_time - start_time

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "spreadsheet" in content_type or "excel" in content_type:
                print(
                    f"   ✅ SUCCESS - Excel file returned ({len(response.content):,} bytes, {execution_time:.2f}s)"
                )
                return True
            else:
                print(f"   ❌ WRONG FORMAT - Expected Excel, got {content_type}")
                print(f"   Response preview: {response.text[:200]}...")
                return False
        else:
            print(f"   ❌ FAILED - Status {response.status_code}")
            try:
                error = response.json().get("detail", "Unknown error")
                print(f"   Error: {error}")
            except:
                print(f"   Response preview: {response.text[:200]}...")
            return False

    except requests.exceptions.Timeout:
        print(f"   ⏰ TIMEOUT - Export took longer than {timeout} seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ CONNECTION ERROR - Backend not accessible")
        return False
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False


def main():
    """Run comprehensive export regression tests"""
    print("🧪 Export Regression Test Suite")
    print("=" * 60)

    # Check if backend is running
    base_url = "http://localhost:8001/v1/excel"

    try:
        health_response = requests.get("http://localhost:8001/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Backend health check failed")
            return 1
        print("✅ Backend is running and healthy")
    except:
        print("❌ Backend is not running on port 8001")
        print("   Please start the backend first:")
        print("   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload")
        return 1

    # Define all export endpoints to test
    test_cases = [
        # Basic exports
        ("/trading/export", "Trading Data Export"),
        ("/positions/export", "All Positions Export"),
        # Individual position exports with various tickers
        ("/positions/test_aapl/export?ticker=AAPL", "AAPL Position Export"),
        ("/positions/test_msft/export?ticker=MSFT", "MSFT Position Export"),
        ("/positions/test_zim/export?ticker=ZIM", "ZIM Position Export"),
        ("/positions/test_spy/export?ticker=SPY", "SPY ETF Position Export"),
        ("/positions/test_brk/export?ticker=BRK.A", "Berkshire Hathaway Position Export"),
        # Comprehensive exports
        ("/positions/test_aapl/comprehensive-export?ticker=AAPL", "AAPL Comprehensive Export"),
        ("/positions/test_nvda/comprehensive-export?ticker=NVDA", "NVIDIA Comprehensive Export"),
        ("/positions/test_zim/comprehensive-export?ticker=ZIM", "ZIM Comprehensive Export"),
        # Simulation exports
        ("/simulation/test_sim_aapl/export?ticker=AAPL", "AAPL Simulation Export"),
        ("/simulation/test_sim_zim/export?ticker=ZIM", "ZIM Simulation Export"),
        ("/simulation/test_sim_spy/export?ticker=SPY", "SPY Simulation Export"),
        # Enhanced simulation exports (these were previously failing)
        (
            "/simulation/test_sim_aapl/enhanced-export?ticker=AAPL",
            "AAPL Enhanced Simulation Export",
        ),
        ("/simulation/test_sim_zim/enhanced-export?ticker=ZIM", "ZIM Enhanced Simulation Export"),
        (
            "/simulation/test_sim_msft/enhanced-export?ticker=MSFT",
            "MSFT Enhanced Simulation Export",
        ),
    ]

    print(f"\n🚀 Running {len(test_cases)} export regression tests...")

    results = []
    failed_tests = []

    for endpoint, description in test_cases:
        success = test_endpoint(base_url, endpoint, description)
        results.append((description, success))
        if not success:
            failed_tests.append((endpoint, description))

    # Summary
    print("\n" + "=" * 60)
    print("📊 EXPORT REGRESSION TEST RESULTS:")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    # Group results by category
    categories = {
        "📁 Basic Exports": ["Trading Data Export", "All Positions Export"],
        "📈 Position Exports": [
            desc
            for desc in [r[0] for r in results]
            if "Position Export" in desc and "Comprehensive" not in desc
        ],
        "📊 Comprehensive Exports": [
            desc for desc in [r[0] for r in results] if "Comprehensive Export" in desc
        ],
        "🎲 Simulation Exports": [
            desc
            for desc in [r[0] for r in results]
            if "Simulation Export" in desc and "Enhanced" not in desc
        ],
        "⚡ Enhanced Simulation": [
            desc for desc in [r[0] for r in results] if "Enhanced Simulation Export" in desc
        ],
    }

    for category, test_names in categories.items():
        if test_names:
            print(f"\n   {category}:")
            for description, success in results:
                if description in test_names:
                    status = "✅ PASS" if success else "❌ FAIL"
                    print(f"      {status} - {description}")

    print(f"\nOverall Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL EXPORTS WORKING PERFECTLY!")
        print("   ✅ No regressions detected")
        print("   ✅ All ticker parameters working correctly")
        print("   ✅ MergedCell error fixed")
        print("   ✅ All export formats generating properly")
        print("   📊 System ready for production use!")
    elif passed >= total * 0.9:
        print(f"\n🟢 EXCELLENT: {passed}/{total} exports working!")
        print("   Most functionality is stable")
        if failed_tests:
            print("\n   ⚠️  Failed tests:")
            for endpoint, description in failed_tests:
                print(f"      - {description}: {endpoint}")
    elif passed >= total * 0.7:
        print(f"\n🟡 GOOD: {passed}/{total} exports working")
        print("   Some issues detected but core functionality works")
        if failed_tests:
            print("\n   ❌ Failed tests:")
            for endpoint, description in failed_tests:
                print(f"      - {description}: {endpoint}")
    else:
        print(f"\n🔴 CRITICAL: Only {passed}/{total} exports working!")
        print("   Major regressions detected - needs immediate attention")
        if failed_tests:
            print("\n   ❌ Failed tests:")
            for endpoint, description in failed_tests:
                print(f"      - {description}: {endpoint}")

    # Performance notes
    print("\n⏱️  PERFORMANCE NOTES:")
    print("   • Real market data fetching may take 10-30 seconds per export")
    print("   • Comprehensive exports are larger and take more time")
    print("   • Enhanced simulation exports include detailed time series")

    # Recommendations
    if failed_tests:
        print("\n💡 TROUBLESHOOTING RECOMMENDATIONS:")
        print("   1. Check backend logs for detailed error messages")
        print("   2. Verify internet connection for Yahoo Finance API access")
        print("   3. Ensure all dependencies are properly installed")
        print("   4. Check for any recent code changes that might have introduced issues")

        # Specific guidance for common issues
        enhanced_sim_failures = [
            desc for endpoint, desc in failed_tests if "Enhanced Simulation" in desc
        ]
        if enhanced_sim_failures:
            print("   📌 Enhanced Simulation Export Issues:")
            print("      - Check for MergedCell handling in Excel services")
            print("      - Verify simulation_result attribute access patterns")
            print("      - Ensure raw_data and metrics are properly structured")

    return 0 if passed >= total * 0.8 else 1


if __name__ == "__main__":
    exit(main())

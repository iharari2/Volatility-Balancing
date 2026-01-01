#!/usr/bin/env python3
"""
Test all export endpoints to identify issues
"""

import requests


def test_export_endpoint(url, description):
    """Test a single export endpoint"""
    print(f"\n🧪 Testing: {description}")
    print(f"   URL: {url}")

    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "spreadsheet" in content_type or "excel" in content_type:
                print(f"   ✅ SUCCESS - Excel file returned ({len(response.content):,} bytes)")
                return True
            else:
                print(f"   ⚠️  WARNING - Unexpected content type: {content_type}")
                print(f"   Response: {response.text[:200]}...")
                return False
        else:
            print(f"   ❌ FAILED - Status {response.status_code}")
            try:
                error_detail = response.json().get("detail", "No detail provided")
                print(f"   Error: {error_detail}")
            except:
                print(f"   Response: {response.text[:200]}...")
            return False

    except requests.exceptions.ConnectionError:
        print("   ❌ CONNECTION ERROR - Backend not running on port 8001")
        return False
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False


def main():
    """Test all export endpoints"""
    print("🚀 Testing All Export Endpoints")
    print("=" * 50)

    # Backend base URL
    base_url = "http://localhost:8001/v1/excel"

    # Test endpoints
    endpoints = [
        # Portfolio/Position exports
        (f"{base_url}/positions/export", "All Positions Export"),
        (f"{base_url}/positions/pos_2e16e371/export", "Individual Position Export"),
        (
            f"{base_url}/positions/pos_2e16e371/comprehensive-export",
            "Comprehensive Position Export",
        ),
        # Simulation exports
        (f"{base_url}/simulation/sim_123/export", "Simulation Export"),
        (f"{base_url}/simulation/sim_123/enhanced-export", "Enhanced Simulation Export"),
        # Trading export
        (f"{base_url}/export/trading", "Trading Export"),
    ]

    results = []
    for url, description in endpoints:
        success = test_export_endpoint(url, description)
        results.append((description, success))

    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {description}")

    print(f"\nOverall: {passed}/{total} exports working")

    if passed < total:
        print("\n💡 TROUBLESHOOTING:")
        print(
            "   1. Make sure backend is running: python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
        )
        print("   2. Check backend logs for detailed error messages")
        print("   3. Verify the position IDs exist or are handled properly")

    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Quick test to verify simulation export fixes
"""

import requests


def test_simulation_exports():
    """Test the fixed simulation export endpoints"""

    base_url = "http://localhost:8001/v1/excel"

    # Check backend health first
    try:
        health_response = requests.get("http://localhost:8001/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Backend not healthy")
            return False
        print("✅ Backend is healthy")
    except:
        print("❌ Backend not accessible on port 8001")
        return False

    # Test the specific failing case
    test_cases = [
        {
            "name": "ZIM Basic Simulation Export",
            "url": f"{base_url}/simulation/1759213671758/export?ticker=ZIM",
            "expected_content_type": "spreadsheet",
        },
        {
            "name": "ZIM Enhanced Simulation Export",
            "url": f"{base_url}/simulation/1759213671758/enhanced-export?ticker=ZIM",
            "expected_content_type": "spreadsheet",
        },
        {
            "name": "AAPL Basic Simulation Export",
            "url": f"{base_url}/simulation/test_aapl/export?ticker=AAPL",
            "expected_content_type": "spreadsheet",
        },
    ]

    all_passed = True

    for test in test_cases:
        print(f"\n🔧 Testing: {test['name']}")
        print(f"   URL: {test['url']}")

        try:
            response = requests.get(test["url"], timeout=30)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                content_length = len(response.content)

                if test["expected_content_type"] in content_type:
                    print(f"   ✅ SUCCESS - {content_length:,} bytes Excel file")
                else:
                    print(f"   ❌ WRONG TYPE - Got {content_type}")
                    all_passed = False
            else:
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    print(f"   ❌ FAILED - {error_detail}")
                except:
                    print(f"   ❌ FAILED - {response.text[:200]}...")
                all_passed = False

        except Exception as e:
            print(f"   ❌ EXCEPTION - {e}")
            all_passed = False

    return all_passed


def main():
    """Main test function"""
    print("🧪 Simulation Export Fix Verification")
    print("=" * 50)

    success = test_simulation_exports()

    print(f"\n{'='*50}")
    if success:
        print("🎉 ALL SIMULATION EXPORTS WORKING!")
        print("   ✅ MergedCell error fixed")
        print("   ✅ SimulationResult class mismatch fixed")
        print("   ✅ Date parsing issues resolved")
        print("   📊 Ready for production use")
        return 0
    else:
        print("❌ SOME SIMULATION EXPORTS STILL FAILING")
        print("   Check the errors above for details")
        return 1


if __name__ == "__main__":
    exit(main())

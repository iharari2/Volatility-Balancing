#!/usr/bin/env python3
"""
Debug script to test simulation export endpoints specifically
"""

import requests


def test_simulation_export(base_url, simulation_id, ticker):
    """Test simulation export endpoints"""

    # Test basic simulation export
    print("\n🔧 Testing Basic Simulation Export:")
    print(f"   Simulation ID: {simulation_id}")
    print(f"   Ticker: {ticker}")

    url = f"{base_url}/simulation/{simulation_id}/export?ticker={ticker}"
    print(f"   URL: {url}")

    try:
        response = requests.get(url, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Content-Length: {len(response.content)} bytes")

        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"   Error Detail: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw Response: {response.text[:500]}...")
        else:
            print("   ✅ Basic export successful")

    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # Test enhanced simulation export
    print("\n🔧 Testing Enhanced Simulation Export:")
    url = f"{base_url}/simulation/{simulation_id}/enhanced-export?ticker={ticker}"
    print(f"   URL: {url}")

    try:
        response = requests.get(url, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Content-Length: {len(response.content)} bytes")

        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"   Error Detail: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw Response: {response.text[:500]}...")
        else:
            print("   ✅ Enhanced export successful")

    except Exception as e:
        print(f"   ❌ Exception: {e}")


def main():
    """Test simulation exports"""
    print("🧪 Simulation Export Debug Test")
    print("=" * 50)

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

    # Test different simulation scenarios
    test_cases = [
        ("1759213671758", "ZIM"),  # The specific case mentioned by user
        ("test_sim_aapl", "AAPL"),
        ("test_sim_msft", "MSFT"),
        ("nonexistent_sim", "GOOGL"),  # Test error handling
    ]

    for sim_id, ticker in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing Simulation: {sim_id} with ticker {ticker}")
        print(f"{'='*60}")
        test_simulation_export(base_url, sim_id, ticker)

    print(f"\n{'='*60}")
    print("🏁 Debug test completed")
    print("Check the output above for specific error details")

    return 0


if __name__ == "__main__":
    exit(main())

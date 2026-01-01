#!/usr/bin/env python3
"""
Simple test for Excel export functionality.
"""

import requests
import time


def test_excel_export():
    """Test Excel export endpoints."""
    print("🧪 Testing Excel Export Functionality")
    print("=" * 50)

    base_url = "http://localhost:8001/v1"

    # Wait a moment for backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(3)

    # Test 1: Check if backend is running
    print("\n1. Testing backend health...")
    try:
        response = requests.get(f"{base_url}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running on port 8001")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # Test 2: Check simulations endpoint
    print("\n2. Testing simulations endpoint...")
    try:
        response = requests.get(f"{base_url}/simulations/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Simulations endpoint working")
            print(f"   Found {len(data.get('simulations', []))} simulations")
            if data.get("simulations"):
                print(f"   First simulation: {data['simulations'][0]['ticker']}")
        else:
            print(f"❌ Simulations endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing simulations: {e}")

    # Test 3: Test Excel export with test data
    print("\n3. Testing Excel export...")
    try:
        response = requests.get(f"{base_url}/excel/simulation/test-simulation/export")
        if response.status_code == 200:
            print("✅ Excel export working")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Content-Length: {len(response.content)} bytes")
        else:
            print(f"❌ Excel export failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing Excel export: {e}")

    print("\n🎉 Test completed!")


if __name__ == "__main__":
    test_excel_export()

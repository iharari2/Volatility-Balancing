#!/usr/bin/env python3
"""
Simple test for Excel export - run this after starting the backend.
"""

import requests


def test_excel_export():
    """Test Excel export with a simple request."""
    print("🧪 Testing Excel Export")
    print("=" * 40)

    base_url = "http://localhost:8001/v1"

    # Test 1: Check backend health
    print("1. Checking backend health...")
    try:
        response = requests.get(f"{base_url}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend not running: {e}")
        print("Please start the backend first:")
        print("  cd backend")
        print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8001")
        return

    # Test 2: Check simulations
    print("\n2. Checking simulations...")
    try:
        response = requests.get(f"{base_url}/simulations/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data.get('simulations', []))} simulations")

            if data.get("simulations"):
                sim_id = data["simulations"][0]["id"]
                print(f"   Testing with simulation: {sim_id}")

                # Test 3: Test Excel export
                print("\n3. Testing Excel export...")
                try:
                    response = requests.get(f"{base_url}/excel/simulations/{sim_id}/export")
                    if response.status_code == 200:
                        print("✅ Excel export working!")
                        print(f"   File size: {len(response.content)} bytes")
                        print(f"   Content type: {response.headers.get('content-type')}")

                        # Save the file for inspection
                        with open("test_export.xlsx", "wb") as f:
                            f.write(response.content)
                        print("   Saved as: test_export.xlsx")
                    else:
                        print(f"❌ Excel export failed: {response.status_code}")
                        print(f"   Error: {response.text}")
                except Exception as e:
                    print(f"❌ Excel export error: {e}")
            else:
                print("   No simulations found - testing with test data...")
                try:
                    response = requests.get(f"{base_url}/excel/simulation/test-simulation/export")
                    if response.status_code == 200:
                        print("✅ Test Excel export working!")
                        print(f"   File size: {len(response.content)} bytes")
                    else:
                        print(f"❌ Test Excel export failed: {response.status_code}")
                except Exception as e:
                    print(f"❌ Test Excel export error: {e}")
        else:
            print(f"❌ Simulations endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n🎉 Test completed!")


if __name__ == "__main__":
    test_excel_export()

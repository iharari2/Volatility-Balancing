#!/usr/bin/env python3
"""
Test script to verify Excel export fixes.
"""

import requests
import time


def test_excel_export_fixes():
    """Test the Excel export fixes."""
    print("🧪 Testing Excel Export Fixes")
    print("=" * 50)

    base_url = "http://localhost:8001/v1"

    # Wait a moment for backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(2)

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
                sim_id = data["simulations"][0]["id"]
                print(f"   First simulation ID: {sim_id}")

                # Test 3: Test regular Excel export
                print("\n3. Testing regular Excel export...")
                try:
                    response = requests.get(f"{base_url}/excel/simulations/{sim_id}/export")
                    if response.status_code == 200:
                        print("✅ Regular Excel export working")
                        print(f"   Content-Type: {response.headers.get('content-type')}")
                        print(f"   Content-Length: {len(response.content)} bytes")
                    else:
                        print(f"❌ Regular Excel export failed: {response.status_code}")
                        print(f"   Response: {response.text}")
                except Exception as e:
                    print(f"❌ Error testing regular Excel export: {e}")

                # Test 4: Test enhanced Excel export
                print("\n4. Testing enhanced Excel export...")
                try:
                    response = requests.get(f"{base_url}/excel/simulation/{sim_id}/enhanced-export")
                    if response.status_code == 200:
                        print("✅ Enhanced Excel export working")
                        print(f"   Content-Type: {response.headers.get('content-type')}")
                        print(f"   Content-Length: {len(response.content)} bytes")
                    else:
                        print(f"❌ Enhanced Excel export failed: {response.status_code}")
                        print(f"   Response: {response.text}")
                except Exception as e:
                    print(f"❌ Error testing enhanced Excel export: {e}")
            else:
                print("   No simulations found - testing with test data...")
                # Test with test data
                print("\n3. Testing Excel export with test data...")
                try:
                    response = requests.get(f"{base_url}/excel/simulation/test-simulation/export")
                    if response.status_code == 200:
                        print("✅ Test Excel export working")
                        print(f"   Content-Type: {response.headers.get('content-type')}")
                        print(f"   Content-Length: {len(response.content)} bytes")
                    else:
                        print(f"❌ Test Excel export failed: {response.status_code}")
                except Exception as e:
                    print(f"❌ Error testing test Excel export: {e}")
        else:
            print(f"❌ Simulations endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing simulations: {e}")

    print("\n🎉 Test completed!")


if __name__ == "__main__":
    test_excel_export_fixes()

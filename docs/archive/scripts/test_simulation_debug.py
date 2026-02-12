#!/usr/bin/env python3
"""
Debug script to test simulation API and identify the "Failed to fetch" issue.
"""

import requests
import json
from datetime import datetime, timedelta


def test_backend_health():
    """Test if backend is running and responding."""
    try:
        response = requests.get("http://localhost:8001/v1/healthz", timeout=5)
        print(f"✅ Backend health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running on port 8001")
        return False
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False


def test_simulation_endpoint():
    """Test the simulation endpoint with a simple request."""
    try:
        # Create a simple simulation request
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last 7 days

        request_data = {
            "ticker": "AAPL",
            "start_date": start_date.isoformat() + "Z",
            "end_date": end_date.isoformat() + "Z",
            "initial_cash": 10000.0,
            "include_after_hours": False,
            "position_config": {
                "trigger_threshold_pct": 0.05,
                "rebalance_ratio": 0.1,
                "commission_rate": 0.001,
                "min_notional": 100.0,
                "allow_after_hours": False,
                "guardrails": {"min_stock_alloc_pct": 0.1, "max_stock_alloc_pct": 0.9},
            },
        }

        print("🧪 Testing simulation endpoint...")
        print(f"   Request: {json.dumps(request_data, indent=2)}")

        response = requests.post(
            "http://localhost:8001/v1/simulation/run", json=request_data, timeout=30
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Simulation successful!")
            print(f"   Simulation ID: {result.get('simulation_id', 'N/A')}")
            print(f"   Final Cash: ${result.get('final_cash', 0):.2f}")
            print(f"   Final Asset Value: ${result.get('final_asset_value', 0):.2f}")
            return True
        else:
            print(f"❌ Simulation failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail}")
            except:
                print(f"   Raw response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Simulation request timed out")
        return False
    except Exception as e:
        print(f"❌ Simulation request failed: {e}")
        return False


def test_cors_headers():
    """Test CORS headers for frontend compatibility."""
    try:
        # Test preflight request
        response = requests.options(
            "http://localhost:8001/v1/simulation/run",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        print(f"✅ CORS preflight: {response.status_code}")

        # Check CORS headers
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
        }
        print(f"   CORS Headers: {cors_headers}")
        return True
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False


def main():
    print("🔍 Debugging Simulation 'Failed to fetch' Error")
    print("=" * 50)

    # Test 1: Backend health
    print("\n1. Testing Backend Health...")
    backend_ok = test_backend_health()

    if not backend_ok:
        print("\n❌ Backend is not running. Please start it with:")
        print("   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001")
        return

    # Test 2: CORS headers
    print("\n2. Testing CORS Headers...")
    test_cors_headers()

    # Test 3: Simulation endpoint
    print("\n3. Testing Simulation Endpoint...")
    simulation_ok = test_simulation_endpoint()

    if simulation_ok:
        print("\n✅ All tests passed! The simulation API is working correctly.")
        print("\nIf you're still getting 'Failed to fetch' in the frontend:")
        print("1. Check that the frontend is running on http://localhost:5173")
        print("2. Check browser console for CORS errors")
        print("3. Verify the API_BASE_URL in frontend/src/lib/api.ts")
    else:
        print("\n❌ Simulation endpoint is not working. Check backend logs for errors.")


if __name__ == "__main__":
    main()

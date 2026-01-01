#!/usr/bin/env python3
"""Test script to verify backend endpoints are working"""

import requests

API_BASE = "http://localhost:8001/api/v1"


def test_endpoints():
    try:
        print("Testing backend endpoints...")

        # Test health check
        try:
            response = requests.get(f"{API_BASE}/../health", timeout=5)
            print(f"Health check: {response.status_code}")
        except:
            print("Health check: Failed")

        # Test positions endpoint
        try:
            response = requests.get(f"{API_BASE}/positions", timeout=5)
            print(f"GET /positions: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                positions = data.get("positions", [])
                print(f"Found {len(positions)} positions")

                # Test comprehensive export for first position if available
                if positions:
                    pos_id = positions[0]["id"]
                    print(f"Testing comprehensive export for position: {pos_id}")

                    export_url = f"{API_BASE}/excel/positions/{pos_id}/comprehensive-export"
                    print(f"Trying: {export_url}")

                    response = requests.get(export_url, timeout=10)
                    print(f"Comprehensive export: {response.status_code}")
                    if response.status_code != 200:
                        print(f"Error response: {response.text}")
                else:
                    print("No positions found for testing comprehensive export")
            else:
                print(f"Error getting positions: {response.text}")
        except Exception as e:
            print(f"Error testing positions: {e}")

        # Test excel export endpoints
        try:
            response = requests.get(f"{API_BASE}/excel/export/formats", timeout=5)
            print(f"Excel formats endpoint: {response.status_code}")
        except Exception as e:
            print(f"Error testing excel formats: {e}")

    except Exception as e:
        print(f"General error: {e}")


if __name__ == "__main__":
    test_endpoints()

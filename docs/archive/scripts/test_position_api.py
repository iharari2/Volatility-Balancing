#!/usr/bin/env python3
"""Test script to verify position API is working"""

import requests
import json

# Test the backend API directly
API_BASE = "http://localhost:8001/api"


def test_positions():
    try:
        # Test GET positions
        response = requests.get(f"{API_BASE}/positions")
        print(f"GET /positions status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Positions data: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")

        # Test creating a position
        position_data = {"ticker": "TEST", "qty": 100.0, "cash": 5000.0, "anchor_price": 50.0}

        response = requests.post(f"{API_BASE}/positions", json=position_data)
        print(f"\nPOST /positions status: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"Created position: {json.dumps(data, indent=2)}")

            # Test updating the position
            update_data = {
                "ticker": "TEST",
                "qty": 150.0,  # Updated quantity
                "cash": 7500.0,  # Updated cash
                "anchor_price": 50.0,
            }

            response = requests.post(f"{API_BASE}/positions", json=update_data)
            print(f"\nUpdate position status: {response.status_code}")
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"Updated position: {json.dumps(data, indent=2)}")
        else:
            print(f"Error creating position: {response.text}")

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to backend. Make sure it's running on port 8001")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_positions()

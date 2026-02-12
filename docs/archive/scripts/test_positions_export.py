#!/usr/bin/env python3
"""
Test positions export specifically
"""

import requests


def test_positions_export():
    """Test positions export"""
    base_url = "http://localhost:8001"

    print("🧪 Testing Positions Export")
    print("=" * 40)

    try:
        # Test positions export
        response = requests.get(f"{base_url}/v1/export/positions")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✅ Positions export successful!")
            print(f"File size: {len(response.content)} bytes")

            # Save the file
            with open("positions_export.xlsx", "wb") as f:
                f.write(response.content)
            print("📁 Saved as: positions_export.xlsx")
        else:
            print(f"❌ Export failed: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_positions_export()

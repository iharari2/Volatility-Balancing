#!/usr/bin/env python3
"""
Demo script to test Excel export functionality
"""

import requests


def test_excel_export():
    """Test the Excel export functionality"""
    base_url = "http://localhost:8001"

    print("🧪 Testing Excel Export Functionality")
    print("=" * 50)

    # Test 1: Export optimization results
    print("\n1. Testing Optimization Results Export...")
    try:
        # First, let's get available optimization configs
        configs_response = requests.get(f"{base_url}/v1/optimization/configs")
        if configs_response.status_code == 200:
            configs = configs_response.json()
            if configs:
                config_id = configs[0]["id"]
                print(f"   Using config ID: {config_id}")

                # Export optimization results
                export_response = requests.get(f"{base_url}/v1/export/optimization/{config_id}")
                if export_response.status_code == 200:
                    print("   ✅ Optimization results export successful!")
                    print(f"   File size: {len(export_response.content)} bytes")

                    # Save the file
                    with open("optimization_results_export.xlsx", "wb") as f:
                        f.write(export_response.content)
                    print("   📁 Saved as: optimization_results_export.xlsx")
                else:
                    print(f"   ❌ Export failed: {export_response.status_code}")
            else:
                print("   ⚠️  No optimization configs found")
        else:
            print(f"   ❌ Failed to get configs: {configs_response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: Export trading data
    print("\n2. Testing Trading Data Export...")
    try:
        export_response = requests.get(f"{base_url}/v1/export/trading")
        if export_response.status_code == 200:
            print("   ✅ Trading data export successful!")
            print(f"   File size: {len(export_response.content)} bytes")

            # Save the file
            with open("trading_data_export.xlsx", "wb") as f:
                f.write(export_response.content)
            print("   📁 Saved as: trading_data_export.xlsx")
        else:
            print(f"   ❌ Export failed: {export_response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Check available endpoints
    print("\n3. Available Excel Export Endpoints:")
    print("   📊 GET /v1/export/optimization/{config_id}")
    print("   📊 GET /v1/export/simulation/{simulation_id}")
    print("   📊 GET /v1/export/trading")
    print("   📊 GET /v1/export/positions")
    print("   📊 GET /v1/export/trades")
    print("   📊 GET /v1/export/orders")


if __name__ == "__main__":
    test_excel_export()

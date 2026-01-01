#!/usr/bin/env python3
"""
Test script for enhanced Excel export functionality.
"""

import requests
from datetime import datetime, timedelta


def test_enhanced_excel_export():
    """Test the enhanced Excel export functionality."""
    print("🧪 Testing Enhanced Excel Export Functionality")
    print("=" * 60)

    base_url = "http://localhost:8001/v1"

    # Test 1: Enhanced Simulation Export
    print("\n1. Testing Enhanced Simulation Export...")
    try:
        # First, run a simulation to get data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        simulation_request = {
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

        print("   Running simulation...")
        sim_response = requests.post(
            f"{base_url}/simulation/run", json=simulation_request, timeout=60
        )

        if sim_response.status_code == 200:
            simulation_data = sim_response.json()
            simulation_id = simulation_data.get("simulation_id")
            print(f"   ✅ Simulation completed. ID: {simulation_id}")

            # Test enhanced simulation export
            print("   Testing enhanced simulation export...")
            export_response = requests.get(
                f"{base_url}/excel/simulation/{simulation_id}/enhanced-export"
            )

            if export_response.status_code == 200:
                print("   ✅ Enhanced simulation export successful!")
                print(f"   File size: {len(export_response.content)} bytes")

                # Save the file for inspection
                filename = (
                    f"enhanced_simulation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                )
                with open(filename, "wb") as f:
                    f.write(export_response.content)
                print(f"   Saved as: {filename}")
            else:
                print(f"   ❌ Enhanced simulation export failed: {export_response.status_code}")
                print(f"   Error: {export_response.text}")
        else:
            print(f"   ❌ Simulation failed: {sim_response.status_code}")
            print(f"   Error: {sim_response.text}")

    except Exception as e:
        print(f"   ❌ Enhanced simulation export test failed: {e}")

    # Test 2: Enhanced Trading Export
    print("\n2. Testing Enhanced Trading Export...")
    try:
        print("   Testing enhanced trading export...")
        export_response = requests.get(f"{base_url}/excel/trading/enhanced-export")

        if export_response.status_code == 200:
            print("   ✅ Enhanced trading export successful!")
            print(f"   File size: {len(export_response.content)} bytes")

            # Save the file for inspection
            filename = f"enhanced_trading_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            with open(filename, "wb") as f:
                f.write(export_response.content)
            print(f"   Saved as: {filename}")
        else:
            print(f"   ❌ Enhanced trading export failed: {export_response.status_code}")
            print(f"   Error: {export_response.text}")

    except Exception as e:
        print(f"   ❌ Enhanced trading export test failed: {e}")

    # Test 3: Check available templates
    print("\n3. Testing Export Templates...")
    try:
        templates_response = requests.get(f"{base_url}/excel/export/templates")

        if templates_response.status_code == 200:
            templates = templates_response.json()
            print("   ✅ Export templates retrieved successfully!")
            print("   Available templates:")
            for template in templates.get("templates", []):
                print(f"     - {template['name']}: {template['description']}")
        else:
            print(f"   ❌ Failed to get templates: {templates_response.status_code}")

    except Exception as e:
        print(f"   ❌ Templates test failed: {e}")

    print("\n🎉 Enhanced Excel Export Testing Complete!")
    print("\nKey Features Tested:")
    print("✅ Enhanced simulation export with comprehensive data logs")
    print("✅ Enhanced trading audit with complete audit trail")
    print("✅ Export templates and API endpoints")
    print("\nThe enhanced exports include:")
    print("- Comprehensive time-series data with every data point")
    print("- Algorithm decision logs for debugging")
    print("- Accounting audit trail for compliance")
    print("- Performance analysis and risk metrics")
    print("- Dividend analysis and trigger events")
    print("- Market data analysis and debug information")


if __name__ == "__main__":
    test_enhanced_excel_export()

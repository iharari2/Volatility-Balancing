#!/usr/bin/env python3
"""
Verify that the simulation export test fix works
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

try:
    from domain.entities.simulation_result import SimulationResult
    from application.services.excel_export_service import ExcelExportService

    print("🚀 Creating mock simulation result...")

    # Create a mock simulation result with all required data
    simulation_result = SimulationResult.create(
        ticker="AAPL",
        start_date="2024-01-01",
        end_date="2024-12-31",
        parameters={
            "trigger_threshold": 0.03,
            "rebalance_threshold": 0.05,
            "max_position_size": 0.2,
        },
        metrics={
            "sharpe_ratio": 1.5,
            "total_return": 0.15,
            "max_drawdown": 0.08,
            "volatility": 0.12,
            "algorithm_pnl": 15000.0,
            "buy_hold_pnl": 12000.0,
            "buy_hold_return_pct": 12.0,
            "buy_hold_volatility": 0.15,
            "buy_hold_sharpe_ratio": 0.8,
            "buy_hold_max_drawdown": 0.12,
            "excess_return": 3.0,
            "alpha": 0.03,
            "beta": 1.1,
            "information_ratio": 0.25,
        },
        raw_data={
            "initial_cash": 100000.0,
            "algorithm_trades": 15,
            "total_dividends_received": 500.0,
            "time_series_data": [
                {
                    "date": "2024-01-01",
                    "price": 150.0,
                    "position_value": 15000.0,
                    "cash_value": 85000.0,
                    "total_value": 100000.0,
                },
            ],
            "trade_log": [
                {
                    "timestamp": "2024-01-15T10:30:00Z",
                    "action": "buy",
                    "quantity": 100,
                    "price": 150.0,
                },
            ],
            "daily_returns": [
                {"date": "2024-01-01", "return": 0.001},
            ],
            "price_data": [
                {"timestamp": "2024-01-01T09:30:00Z", "price": 150.0, "volume": 1000000},
            ],
        },
    )

    print("✅ Mock simulation result created successfully")
    print(f"   ID: {simulation_result.id}")
    print(f"   Ticker: {simulation_result.ticker}")
    print(f"   Metrics keys: {list(simulation_result.metrics.keys())}")
    print(f"   Raw data keys: {list(simulation_result.raw_data.keys())}")

    print("\n🚀 Testing Excel export service...")

    # Test the export service
    export_service = ExcelExportService()
    excel_data = export_service.export_simulation_results(simulation_result, "AAPL")

    print("✅ Excel export completed successfully!")
    print(f"   Generated Excel file size: {len(excel_data):,} bytes")

    # Save the file for verification
    with open("test_simulation_export_verification.xlsx", "wb") as f:
        f.write(excel_data)

    print("   Saved as: test_simulation_export_verification.xlsx")
    print("\n🎉 All tests passed! The simulation export fix is working correctly.")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

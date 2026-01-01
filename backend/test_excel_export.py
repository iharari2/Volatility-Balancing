#!/usr/bin/env python3
"""
Test script for Excel export functionality
"""

import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application.services.excel_export_service import ExcelExportService
from application.services.excel_template_service import ExcelTemplateService
from domain.entities.optimization_result import (
    OptimizationResult,
    OptimizationResults,
    ParameterCombination,
    OptimizationResultStatus,
)
from domain.entities.simulation_result import SimulationResult
from domain.value_objects.optimization_criteria import OptimizationMetric


def create_mock_optimization_results():
    """Create mock optimization results for testing."""
    config_id = uuid4()
    results = []

    # Create mock parameter combinations
    for i in range(10):
        combination_id = f"combo_{i+1}"
        parameters = {
            "trigger_threshold": 0.01 + (i * 0.005),
            "rebalance_threshold": 0.02 + (i * 0.01),
            "max_position_size": 0.1 + (i * 0.05),
        }

        param_combo = ParameterCombination(
            parameters=parameters,
            combination_id=combination_id,
            created_at=datetime.now(timezone.utc),
        )

        # Create mock metrics
        metrics = {
            OptimizationMetric.SHARPE_RATIO: 1.0 + (i * 0.1),
            OptimizationMetric.TOTAL_RETURN: 0.05 + (i * 0.02),
            OptimizationMetric.MAX_DRAWDOWN: 0.1 - (i * 0.01),
            OptimizationMetric.VOLATILITY: 0.15 + (i * 0.01),
        }

        result = OptimizationResult(
            id=uuid4(),
            config_id=config_id,
            parameter_combination=param_combo,
            metrics=metrics,
            status=OptimizationResultStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            execution_time_seconds=10.0 + i,
        )

        results.append(result)

    return OptimizationResults(config_id=config_id, results=results)


def create_mock_simulation_result():
    """Create mock simulation result for testing."""
    return SimulationResult.create(
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
                {
                    "date": "2024-01-02",
                    "price": 151.0,
                    "position_value": 15100.0,
                    "cash_value": 84900.0,
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
                {
                    "timestamp": "2024-02-15T14:45:00Z",
                    "action": "sell",
                    "quantity": 50,
                    "price": 155.0,
                },
                {
                    "timestamp": "2024-03-15T09:15:00Z",
                    "action": "buy",
                    "quantity": 75,
                    "price": 148.0,
                },
            ],
            "daily_returns": [
                {"date": "2024-01-01", "return": 0.001},
                {"date": "2024-01-02", "return": -0.002},
                {"date": "2024-01-03", "return": 0.003},
            ],
            "price_data": [
                {"timestamp": "2024-01-01T09:30:00Z", "price": 150.0, "volume": 1000000},
                {"timestamp": "2024-01-01T09:31:00Z", "price": 150.5, "volume": 500000},
                {"timestamp": "2024-01-01T09:32:00Z", "price": 149.8, "volume": 750000},
            ],
        },
    )


def create_mock_trading_data():
    """Create mock trading data for testing."""
    positions_data = [
        {
            "id": "pos_1",
            "ticker": "AAPL",
            "shares": 100,
            "cash_balance": 5000.0,
            "created_at": "2024-01-01T09:00:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
        },
        {
            "id": "pos_2",
            "ticker": "MSFT",
            "shares": 50,
            "cash_balance": 3000.0,
            "created_at": "2024-01-02T09:00:00Z",
            "updated_at": "2024-01-16T11:15:00Z",
        },
    ]

    trades_data = [
        {
            "id": "trade_1",
            "position_id": "pos_1",
            "ticker": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": 150.0,
            "timestamp": "2024-01-15T10:30:00Z",
            "status": "filled",
        },
        {
            "id": "trade_2",
            "position_id": "pos_2",
            "ticker": "MSFT",
            "side": "buy",
            "quantity": 50,
            "price": 300.0,
            "timestamp": "2024-01-16T11:15:00Z",
            "status": "filled",
        },
    ]

    orders_data = [
        {
            "id": "order_1",
            "position_id": "pos_1",
            "ticker": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": 150.0,
            "status": "filled",
            "created_at": "2024-01-15T10:30:00Z",
        },
        {
            "id": "order_2",
            "position_id": "pos_2",
            "ticker": "MSFT",
            "side": "buy",
            "quantity": 50,
            "price": 300.0,
            "status": "filled",
            "created_at": "2024-01-16T11:15:00Z",
        },
    ]

    return positions_data, trades_data, orders_data


def test_optimization_export():
    """Test optimization results export."""
    print("Testing optimization results export...")

    # Create mock data
    results = create_mock_optimization_results()

    # Test basic export service
    export_service = ExcelExportService()
    excel_data = export_service.export_optimization_results(results, "Test Optimization")

    # Save to file
    with open("test_optimization_export.xlsx", "wb") as f:
        f.write(excel_data)

    print(f"✅ Optimization export test completed. File size: {len(excel_data)} bytes")
    print("   Saved as: test_optimization_export.xlsx")


def test_simulation_export():
    """Test simulation results export."""
    print("Testing simulation results export...")

    # Create mock data
    simulation_result = create_mock_simulation_result()

    # Test basic export service
    export_service = ExcelExportService()
    excel_data = export_service.export_simulation_results(simulation_result, "AAPL")

    # Save to file
    with open("test_simulation_export.xlsx", "wb") as f:
        f.write(excel_data)

    print(f"✅ Simulation export test completed. File size: {len(excel_data)} bytes")
    print("   Saved as: test_simulation_export.xlsx")


def test_trading_export():
    """Test trading data export."""
    print("Testing trading data export...")

    # Create mock data
    positions_data, trades_data, orders_data = create_mock_trading_data()

    # Test basic export service
    export_service = ExcelExportService()
    excel_data = export_service.export_trading_data(
        positions_data, trades_data, orders_data, "Test Trading Data Export"
    )

    # Save to file
    with open("test_trading_export.xlsx", "wb") as f:
        f.write(excel_data)

    print(f"✅ Trading export test completed. File size: {len(excel_data)} bytes")
    print("   Saved as: test_trading_export.xlsx")


def test_template_service():
    """Test template service directly."""
    print("Testing template service...")

    # Create mock data
    results = create_mock_optimization_results()

    # Test template service
    template_service = ExcelTemplateService()
    excel_data = template_service.create_optimization_report(results, "Template Test")

    # Save to file
    with open("test_template_export.xlsx", "wb") as f:
        f.write(excel_data)

    print(f"✅ Template service test completed. File size: {len(excel_data)} bytes")
    print("   Saved as: test_template_export.xlsx")


def main():
    """Run all Excel export tests."""
    print("🚀 Starting Excel Export Tests")
    print("=" * 50)

    try:
        # Test basic export service
        test_optimization_export()
        print()

        test_simulation_export()
        print()

        test_trading_export()
        print()

        # Test template service
        test_template_service()
        print()

        print("🎉 All Excel export tests completed successfully!")
        print("\nGenerated files:")
        print("  - test_optimization_export.xlsx")
        print("  - test_simulation_export.xlsx")
        print("  - test_trading_export.xlsx")
        print("  - test_template_export.xlsx")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Test the comprehensive export endpoint
"""

import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

try:
    from application.services.comprehensive_excel_export_service import (
        ComprehensiveExcelExportService,
    )
    from domain.entities.position import Position
    from domain.value_objects.guardrails import GuardrailPolicy
    from domain.value_objects.order_policy import OrderPolicy

    print("🚀 Testing comprehensive export endpoint...")

    # Create a mock position
    mock_position = Position(
        id="pos_test123",
        ticker="AAPL",
        qty=100.0,
        cash=5000.0,
        anchor_price=145.0,
        dividend_receivable=0.0,
        withholding_tax_rate=0.25,
        guardrails=GuardrailPolicy(
            min_stock_alloc_pct=0.25,
            max_stock_alloc_pct=0.75,
        ),
        order_policy=OrderPolicy(
            trigger_threshold_pct=0.03,
            rebalance_ratio=1.66667,
            min_qty=1.0,
            commission_rate=0.0001,
            allow_after_hours=True,
        ),
    )

    print("✅ Mock position created successfully")
    print(f"   ID: {mock_position.id}")
    print(f"   Ticker: {mock_position.ticker}")
    print(f"   Qty: {mock_position.qty}")
    print(f"   Cash: {mock_position.cash}")
    print(f"   Anchor Price: {mock_position.anchor_price}")

    # Test the comprehensive service directly
    comprehensive_service = ComprehensiveExcelExportService()

    # Create a compatible position object for the comprehensive service
    compatible_position = type(
        "Position",
        (),
        {
            "ticker": mock_position.ticker,
            "name": f"{mock_position.ticker} Inc.",
            "currentPrice": (mock_position.anchor_price or 150.0) * 1.02,
            "anchorPrice": mock_position.anchor_price or 150.0,
            "units": mock_position.qty,
            "cashAmount": mock_position.cash,
            "assetAmount": mock_position.qty * ((mock_position.anchor_price or 150.0) * 1.02),
            "marketValue": mock_position.qty * ((mock_position.anchor_price or 150.0) * 1.02),
            "pnl": mock_position.qty * ((mock_position.anchor_price or 150.0) * 1.02)
            - mock_position.qty * (mock_position.anchor_price or 150.0),
            "pnlPercent": 2.0,
            "isActive": True,
            "config": type(
                "Config",
                (),
                {
                    "buyTrigger": -mock_position.order_policy.trigger_threshold_pct,
                    "sellTrigger": mock_position.order_policy.trigger_threshold_pct,
                    "lowGuardrail": mock_position.guardrails.min_stock_alloc_pct,
                    "highGuardrail": mock_position.guardrails.max_stock_alloc_pct,
                    "rebalanceRatio": mock_position.order_policy.rebalance_ratio,
                    "minQuantity": mock_position.order_policy.min_qty,
                    "commission": mock_position.order_policy.commission_rate,
                    "dividendTax": mock_position.withholding_tax_rate,
                    "tradeAfterHours": mock_position.order_policy.allow_after_hours,
                },
            )(),
        },
    )()

    print("\n🚀 Testing comprehensive Excel export service...")

    # Test the export service
    excel_data = comprehensive_service.export_position_comprehensive_data(
        position=compatible_position,
        market_data=None,
        transaction_data=None,
        simulation_data=None,
    )

    print("✅ Comprehensive Excel export completed successfully!")
    print(f"   Generated Excel file size: {len(excel_data):,} bytes")

    # Save the file for verification
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_comprehensive_export_{timestamp}.xlsx"
    with open(filename, "wb") as f:
        f.write(excel_data)

    print(f"   Saved as: {filename}")
    print("\n🎉 Comprehensive export test completed successfully!")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

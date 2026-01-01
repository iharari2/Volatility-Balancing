#!/usr/bin/env python3
"""
Test script to verify portfolio persistence works correctly.

This script:
1. Creates a position with SQL persistence
2. Simulates a trade execution
3. Verifies data persists across "restarts"
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up SQL persistence
os.environ["APP_PERSISTENCE"] = "sql"
os.environ["APP_EVENTS"] = "sql"
os.environ["APP_AUTO_CREATE"] = "true"
os.environ["SQL_URL"] = "sqlite:///./test_vb.sqlite"

from app.di import container
from application.dto.orders import FillOrderRequest


def test_persistence():
    """Test that portfolios and trades persist correctly."""
    print("🧪 Testing Portfolio Persistence")
    print("=" * 50)

    # Create a position
    print("1. Creating position...")
    position = container.positions.create(
        tenant_id="default",
        portfolio_id="test_portfolio",
        asset_symbol="AAPL",
        qty=10.0,
    )
    print(f"   ✅ Created position: {position.id}")

    # Submit an order
    print("2. Submitting order...")
    from application.use_cases.submit_order_uc import SubmitOrderUC

    submit_uc = SubmitOrderUC(
        positions=container.positions,
        orders=container.orders,
        events=container.events,
        idempotency=container.idempotency,
        clock=container.clock,
    )

    from application.dto.orders import CreateOrderRequest

    order_response = submit_uc.execute(
        position_id=position.id,
        request=CreateOrderRequest(side="BUY", qty=5.0),
        idempotency_key="test_key_1",
    )
    print(f"   ✅ Created order: {order_response.order_id}")

    # Execute the order (simulate trade)
    print("3. Executing trade...")
    from application.use_cases.execute_order_uc import ExecuteOrderUC

    execute_uc = ExecuteOrderUC(
        positions=container.positions,
        orders=container.orders,
        trades=container.trades,
        events=container.events,
        clock=container.clock,
    )

    fill_response = execute_uc.execute(
        order_id=order_response.order_id,
        request=FillOrderRequest(qty=5.0, price=150.0, commission=1.0),
    )
    print(f"   ✅ Executed trade: {fill_response.status}")

    # Verify data exists
    print("4. Verifying data...")
    trades = container.trades.list_for_position(position.id)
    print(f"   ✅ Found {len(trades)} trades for position")

    if trades:
        trade = trades[0]
        print(f"   📊 Trade details: {trade.side} {trade.qty} @ ${trade.price}")

    # Simulate "restart" by creating new container
    print("5. Simulating restart...")
    from app.di import _Container

    new_container = _Container()

    # Check if data persists
    persisted_position = new_container.positions.get(position.id)
    if persisted_position:
        print(
            f"   ✅ Position persisted: {persisted_position.ticker} - {persisted_position.qty} shares"
        )
    else:
        print("   ❌ Position not found after restart")
        return False

    persisted_trades = new_container.trades.list_for_position(position.id)
    if persisted_trades:
        print(f"   ✅ Trades persisted: {len(persisted_trades)} trades found")
    else:
        print("   ❌ No trades found after restart")
        return False

    print("\n🎉 All tests passed! Portfolio persistence is working correctly.")
    return True


if __name__ == "__main__":
    success = test_persistence()
    sys.exit(0 if success else 1)

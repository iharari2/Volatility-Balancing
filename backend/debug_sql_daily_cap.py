#!/usr/bin/env python3
"""Debug script to test daily cap functionality with SQL persistence"""

import os
os.environ.setdefault("APP_PERSISTENCE", "sql")
os.environ.setdefault("APP_EVENTS", "sql")
os.environ.setdefault("APP_IDEMPOTENCY", "memory")
os.environ.setdefault("SQL_URL", "sqlite:///./debug_test.sqlite")
os.environ.setdefault("APP_AUTO_CREATE", "1")

from app.di import container
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.dto.orders import CreateOrderRequest
from domain.errors import GuardrailBreach

def test_daily_cap_sql():
    print("=== Testing Daily Cap Functionality with SQL ===")
    
    # Create position with daily cap of 1
    pos = container.positions.create(ticker="TEST", qty=0.0, cash=1000.0)
    print(f"Position created: {pos.id}")
    print(f"Default max_orders_per_day: {pos.guardrails.max_orders_per_day}")
    
    # Set daily cap to 1
    pos.guardrails.max_orders_per_day = 1
    container.positions.save(pos)
    
    # Verify the save worked
    pos_after = container.positions.get(pos.id)
    print(f"After save max_orders_per_day: {pos_after.guardrails.max_orders_per_day}")
    
    # Check current order count
    today = container.clock.now().date()
    current_count = container.orders.count_for_position_on_day(pos.id, today)
    print(f"Current orders today: {current_count}")
    
    # Create SubmitOrderUC
    uc = SubmitOrderUC(
        positions=container.positions,
        orders=container.orders,
        idempotency=container.idempotency,
        events=container.events,
        clock=container.clock,
    )
    
    # Submit first order (should work)
    print("\n--- Submitting first order ---")
    try:
        resp1 = uc.execute(
            position_id=pos.id,
            request=CreateOrderRequest(side="BUY", qty=1.0),
            idempotency_key="test-1"
        )
        print(f"First order submitted: {resp1.order_id}")
    except Exception as e:
        print(f"First order failed: {e}")
    
    # Check count after first order
    count_after_1 = container.orders.count_for_position_on_day(pos.id, today)
    print(f"Orders after first: {count_after_1}")
    
    # Submit second order (should fail)
    print("\n--- Submitting second order ---")
    try:
        resp2 = uc.execute(
            position_id=pos.id,
            request=CreateOrderRequest(side="BUY", qty=1.0),
            idempotency_key="test-2"
        )
        print(f"Second order submitted: {resp2.order_id} - THIS SHOULD NOT HAPPEN!")
    except GuardrailBreach as e:
        print(f"Second order correctly rejected: {e}")
    except Exception as e:
        print(f"Second order failed with unexpected error: {e}")

if __name__ == "__main__":
    test_daily_cap_sql()

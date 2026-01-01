#!/usr/bin/env python3
"""
Generate a test audit event to verify the audit trail logging system.

Usage:
    python tools/generate_test_audit_event.py
"""

import sys
from pathlib import Path

# Add backend to path - handle both project root and backend/ execution
script_dir = Path(__file__).parent
project_root = script_dir.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from application.events import EventRecord, EventType
from infrastructure.logging.json_event_logger import JsonFileEventLogger
from datetime import datetime
import uuid


def main():
    """Generate a test audit event."""
    # Create logs directory if it doesn't exist
    log_dir = backend_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "audit_trail.jsonl"
    logger = JsonFileEventLogger(log_file)

    # Generate a test trace
    trace_id = str(uuid.uuid4())

    # Create a sequence of test events
    print(f"Generating test audit events with trace_id: {trace_id}")

    # Price event
    price_event = EventRecord.new(
        event_type=EventType.PRICE_EVENT,
        asset_id="AAPL",
        tenant_id="test_tenant",
        portfolio_id="test_portfolio",
        trace_id=trace_id,
        payload={"price": 150.0, "anchor_price": 100.0, "timestamp": datetime.now().isoformat()},
    )
    logger.log_event(price_event)
    print(f"  ✓ Created PriceEvent: {price_event.event_id}")

    # Trigger evaluation
    trigger_event = EventRecord.new(
        event_type=EventType.TRIGGER_EVALUATED,
        asset_id="AAPL",
        tenant_id="test_tenant",
        portfolio_id="test_portfolio",
        trace_id=trace_id,
        parent_event_id=price_event.event_id,
        payload={"fired": True, "direction": "BUY", "reason": "BELOW_THRESHOLD", "threshold": 0.05},
    )
    logger.log_event(trigger_event)
    print(f"  ✓ Created TriggerEvaluated: {trigger_event.event_id}")

    # Guardrail evaluation
    guardrail_event = EventRecord.new(
        event_type=EventType.GUARDRAIL_EVALUATED,
        asset_id="AAPL",
        tenant_id="test_tenant",
        portfolio_id="test_portfolio",
        trace_id=trace_id,
        parent_event_id=trigger_event.event_id,
        payload={
            "allowed": True,
            "reason": "within limits",
            "trade_intent": {"direction": "BUY", "quantity": 20, "price": 150.0},
        },
    )
    logger.log_event(guardrail_event)
    print(f"  ✓ Created GuardrailEvaluated: {guardrail_event.event_id}")

    # Order creation
    order_event = EventRecord.new(
        event_type=EventType.ORDER_CREATED,
        asset_id="AAPL",
        tenant_id="test_tenant",
        portfolio_id="test_portfolio",
        trace_id=trace_id,
        parent_event_id=guardrail_event.event_id,
        payload={
            "order_id": str(uuid.uuid4()),
            "direction": "BUY",
            "quantity": 20,
            "price": 150.0,
            "commission_est": 1.94,
        },
    )
    logger.log_event(order_event)
    print(f"  ✓ Created OrderCreated: {order_event.event_id}")

    print("\n✅ Test events generated successfully!")
    print(f"   Log file: {log_file}")
    print(f"   Trace ID: {trace_id}")
    print("\n   View in Streamlit: streamlit run ui/audit_viewer.py")
    print(f"   View via CLI: python tools/print_audit_trail.py --trace-id {trace_id}")


if __name__ == "__main__":
    main()

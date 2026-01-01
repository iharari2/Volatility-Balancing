#!/usr/bin/env python3
"""
CLI tool to print audit trail for a specific trace_id.

Usage:
    python tools/print_audit_trail.py --trace-id <uuid>
    python tools/print_audit_trail.py --trace-id <uuid> --log-file backend/logs/audit_trail.jsonl
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


DEFAULT_LOG_FILE = Path("backend/logs/audit_trail.jsonl")
DATE_FORMAT = "%H:%M:%S"


def load_events(log_file: Path) -> List[Dict[str, Any]]:
    """Load events from JSONL file."""
    events = []
    if not log_file.exists():
        print(f"Error: Log file not found: {log_file}", file=sys.stderr)
        return events

    with open(log_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {line_num}: {e}", file=sys.stderr)
                continue

    return events


def filter_by_trace_id(events: List[Dict[str, Any]], trace_id: str) -> List[Dict[str, Any]]:
    """Filter events by trace_id."""
    return [e for e in events if e.get("trace_id") == trace_id]


def build_event_chain(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build event chain following parent_event_id relationships."""
    if not events:
        return []

    event_map = {e["event_id"]: e for e in events}

    # Find root event (no parent or parent not in this trace)
    root = None
    for event in events:
        parent_id = event.get("parent_event_id")
        if not parent_id or parent_id not in event_map:
            root = event
            break

    if not root:
        # No root found, just return sorted by time
        return sorted(events, key=lambda e: e["created_at"])

    # Build chain
    chain = [root]
    current = root

    while True:
        # Find child
        child = None
        for event in events:
            if event.get("parent_event_id") == current["event_id"]:
                child = event
                break

        if not child:
            break

        chain.append(child)
        current = child

    return chain


def format_event(event: Dict[str, Any]) -> str:
    """Format event for display."""
    try:
        dt = datetime.fromisoformat(event["created_at"])
        time_str = dt.strftime(DATE_FORMAT)
    except:
        time_str = event["created_at"]

    event_type = event["event_type"]
    payload = event.get("payload", {})

    lines = [f"[{time_str}] {event_type}"]

    # Format based on event type
    if event_type == "PriceEvent":
        price = payload.get("price", "N/A")
        anchor = payload.get("anchor_price", "N/A")
        lines.append(f"  price={price} anchor={anchor}")

    elif event_type == "TriggerEvaluated":
        decision = payload.get("trigger_decision", {})
        fired = decision.get("fired", False)
        direction = decision.get("direction", "N/A")
        reason = decision.get("reason", "N/A")
        if fired:
            lines.append(f"  {direction} trigger fired: {reason}")
        else:
            lines.append(f"  No trigger: {reason}")

    elif event_type == "GuardrailEvaluated":
        decision = payload.get("decision", {})
        allowed = decision.get("allowed", False)
        reason = decision.get("reason", "N/A")
        if allowed:
            trade_intent = decision.get("trade_intent")
            if trade_intent:
                side = trade_intent.get("side", "N/A")
                qty = trade_intent.get("qty", "N/A")
                lines.append(f"  Guardrail allowed {side} {qty}: {reason}")
            else:
                lines.append(f"  Guardrail allowed: {reason}")
        else:
            lines.append(f"  Guardrail DENIED: {reason}")

    elif event_type == "OrderCreated":
        order_id = payload.get("order_id") or payload.get("sim_order_id", "N/A")
        trade_intent = payload.get("trade_intent", {})
        side = trade_intent.get("side", "N/A")
        qty = trade_intent.get("qty", "N/A")
        quote = payload.get("quote", {})
        price = quote.get("price", "N/A")
        commission_est = payload.get("commission_estimate", "N/A")
        lines.append(f"  Order {order_id} {side} {qty} @ {price} commission_est {commission_est}")

    elif event_type == "ExecutionRecorded":
        trade_id = payload.get("trade_id", "N/A")
        side = payload.get("side", "N/A")
        qty = payload.get("qty", "N/A")
        price = payload.get("price", "N/A")
        commission = payload.get("commission", "N/A")
        lines.append(f"  Execution {trade_id} {side} {qty} @ {price} commission {commission}")

    elif event_type == "PositionUpdated":
        before = payload.get("before", {})
        after = payload.get("after", {})
        qty_before = before.get("qty", "N/A")
        qty_after = after.get("qty", "N/A")
        cash_before = before.get("cash", "N/A")
        cash_after = after.get("cash", "N/A")
        lines.append(f"  Position qty {qty_before}→{qty_after} cash {cash_before}→{cash_after}")

    elif event_type == "DividendPaid":
        amount = payload.get("amount", "N/A")
        lines.append(f"  Dividend paid: {amount}")

    else:
        # Generic format
        lines.append(f"  {json.dumps(payload, indent=2)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Print audit trail for a trace_id")
    parser.add_argument("--trace-id", required=True, help="Trace ID to filter events")
    parser.add_argument("--log-file", default=str(DEFAULT_LOG_FILE), help="Path to audit log file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    log_file = Path(args.log_file)
    events = load_events(log_file)

    if not events:
        print(f"No events found in {log_file}", file=sys.stderr)
        sys.exit(1)

    filtered = filter_by_trace_id(events, args.trace_id)

    if not filtered:
        print(f"No events found for trace_id: {args.trace_id}", file=sys.stderr)
        sys.exit(1)

    chain = build_event_chain(filtered)

    if args.json:
        print(json.dumps(chain, indent=2))
    else:
        print(f"Audit Trail for Trace ID: {args.trace_id}")
        print(f"Total events: {len(chain)}\n")
        print("-" * 80)
        for event in chain:
            print(format_event(event))
            print()


if __name__ == "__main__":
    main()

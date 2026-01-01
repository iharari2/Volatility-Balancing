# =========================
# backend/application/helpers/position_event_builder.py
# =========================
"""
Helper to create PositionEvent records from PositionEvaluationTimeline.

PositionEvent is a simplified immutable log for quick queries and audit trails.
This helper extracts the essential fields from the comprehensive timeline.
"""

from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timezone
from uuid import uuid4


def build_position_event_from_timeline(timeline_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a PositionEvent record from a PositionEvaluationTimeline row.

    This creates a simplified immutable log entry with only the essential fields
    for quick queries and audit trails.

    Args:
        timeline_row: Dictionary from PositionEvaluationTimelineModel

    Returns:
        Dictionary ready to be saved to PositionEvent table
    """
    # Map evaluation_type to event_type
    evaluation_type = timeline_row.get("evaluation_type", "DAILY_CHECK")
    event_type_map = {
        "PRICE_UPDATE": "PRICE",
        "DAILY_CHECK": "PRICE",  # Daily checks are price events
        "TRADE_INTENT": "ORDER",
        "EXECUTION": "TRADE",
        "DIVIDEND": "PRICE",  # Dividend events are price-related
    }
    event_type = event_type_map.get(evaluation_type, "PRICE")

    # Map action to event_type if needed
    # PositionEvent table only allows: BUY, SELL, NONE
    # Map HOLD and SKIP to NONE
    raw_action = timeline_row.get("action", "NONE")
    action = raw_action if raw_action in ("BUY", "SELL", "NONE") else "NONE"

    if raw_action in ("BUY", "SELL") and event_type == "PRICE":
        # If there's a trade intent, it's an ORDER event
        if timeline_row.get("trade_intent_qty"):
            event_type = "ORDER"
        # If there's an execution, it's a TRADE event
        if timeline_row.get("trade_id"):
            event_type = "TRADE"

    # Determine if trigger or guardrail evaluation occurred
    if timeline_row.get("trigger_fired"):
        if event_type == "PRICE":
            event_type = "TRIGGER"
    if timeline_row.get("guardrail_block_reason"):
        if event_type in ("PRICE", "TRIGGER"):
            event_type = "GUARDRAIL"

    # Build the event record
    event_data = {
        "event_id": f"evt_{uuid4().hex[:16]}",
        "position_id": timeline_row.get("position_id"),
        "timestamp": timeline_row.get("timestamp") or datetime.now(timezone.utc),
        "event_type": event_type,
        "effective_price": timeline_row.get("effective_price"),
        "action": action,
        "action_reason": timeline_row.get("action_reason"),
        "qty_before": timeline_row.get("position_qty_before", 0.0),
        "qty_after": timeline_row.get("position_qty_after")
        or timeline_row.get("position_qty_before", 0.0),
        "cash_before": timeline_row.get("position_cash_before", 0.0),
        "cash_after": timeline_row.get("position_cash_after")
        or timeline_row.get("position_cash_before", 0.0),
        "total_value_after": timeline_row.get("position_total_value_after")
        or timeline_row.get("position_total_value_before", 0.0),
    }

    return event_data

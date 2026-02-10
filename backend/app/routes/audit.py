# =========================
# backend/app/routes/audit.py
# =========================
"""Audit Trail API endpoints for reading event logs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/v1/audit", tags=["audit"])

# Default log file path - can be overridden for testing
AUDIT_LOG_PATH = Path("logs/audit_trail.jsonl")


class TraceEvent(BaseModel):
    """Individual event within a trace."""
    event_id: str
    event_type: str
    timestamp: str
    payload: dict[str, Any]


class TraceSummary(BaseModel):
    """Summary of a trace for list view."""
    trace_id: str
    time: str
    asset: str
    summary: str
    source: str
    event_count: int


class TraceDetail(BaseModel):
    """Full trace detail with events."""
    trace_id: str
    time: str
    asset: str
    summary: str
    source: str
    events: list[TraceEvent]


class TracesResponse(BaseModel):
    """Response for list traces endpoint."""
    traces: list[TraceSummary]
    total: int
    has_more: bool


def _read_audit_log(log_path: Path = AUDIT_LOG_PATH) -> list[dict]:
    """Read all events from the audit log file."""
    events = []
    if not log_path.exists():
        return events

    try:
        with log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        pass

    return events


def _group_by_trace(events: list[dict]) -> dict[str, list[dict]]:
    """Group events by trace_id."""
    traces = defaultdict(list)
    for event in events:
        trace_id = event.get("trace_id")
        if trace_id:
            traces[trace_id].append(event)

    # Sort events within each trace by timestamp
    for trace_id in traces:
        traces[trace_id].sort(key=lambda e: e.get("created_at", ""))

    return dict(traces)


def _get_trace_summary(events: list[dict]) -> str:
    """Generate a summary string from trace events."""
    if not events:
        return "No events"

    event_types = [e.get("event_type", "Unknown") for e in events]

    # Check for specific patterns
    if "ExecutionRecorded" in event_types:
        # Find the execution event
        for e in events:
            if e.get("event_type") == "ExecutionRecorded":
                payload = e.get("payload", {})
                side = payload.get("side", "Unknown")
                qty = payload.get("quantity", 0)
                return f"Trade executed: {side} {qty} shares"

    if "TriggerEvaluated" in event_types:
        # Find the trigger event
        for e in events:
            if e.get("event_type") == "TriggerEvaluated":
                payload = e.get("payload", {})
                decision = payload.get("trigger_decision", {})
                if decision.get("fired"):
                    direction = decision.get("direction", "unknown")
                    return f"Trigger fired: {direction}"
                else:
                    reason = decision.get("reason", "within thresholds")
                    return f"No trigger: {reason}"

    if "PriceEvent" in event_types:
        return "Price check"

    if "Error" in " ".join(event_types):
        return "Error occurred"

    # Default: list event types
    unique_types = list(dict.fromkeys(event_types))[:3]
    return ", ".join(unique_types)


def _filter_traces(
    traces: dict[str, list[dict]],
    asset: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> dict[str, list[dict]]:
    """Filter traces based on criteria."""
    filtered = {}

    for tid, events in traces.items():
        if not events:
            continue

        # Filter by trace_id if specified
        if trace_id and tid != trace_id:
            continue

        first_event = events[0]

        # Filter by asset
        if asset:
            event_asset = first_event.get("asset_id", "")
            if event_asset.lower() != asset.lower():
                continue

        # Filter by source
        if source and source != "any":
            event_source = first_event.get("source", "")
            if event_source.lower() != source.lower():
                continue

        # Filter by date range
        event_time = first_event.get("created_at", "")
        if event_time:
            try:
                event_dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))

                if start_date:
                    start_dt = datetime.fromisoformat(start_date)
                    if event_dt.date() < start_dt.date():
                        continue

                if end_date:
                    end_dt = datetime.fromisoformat(end_date)
                    if event_dt.date() > end_dt.date():
                        continue
            except ValueError:
                pass

        filtered[tid] = events

    return filtered


@router.get("/traces", response_model=TracesResponse)
async def list_traces(
    asset: Optional[str] = Query(None, description="Filter by asset/ticker"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    source: Optional[str] = Query(None, description="Filter by source (worker, manual, simulation)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of traces to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> TracesResponse:
    """
    List audit traces with optional filtering.

    Traces are grouped by trace_id and sorted by most recent first.
    """
    events = _read_audit_log()
    traces = _group_by_trace(events)
    filtered = _filter_traces(traces, asset=asset, start_date=start_date, end_date=end_date, source=source)

    # Sort traces by most recent event first
    sorted_trace_ids = sorted(
        filtered.keys(),
        key=lambda tid: filtered[tid][-1].get("created_at", "") if filtered[tid] else "",
        reverse=True
    )

    total = len(sorted_trace_ids)
    paginated_ids = sorted_trace_ids[offset:offset + limit]

    summaries = []
    for tid in paginated_ids:
        events_for_trace = filtered[tid]
        if not events_for_trace:
            continue

        first_event = events_for_trace[0]
        summaries.append(TraceSummary(
            trace_id=tid,
            time=first_event.get("created_at", ""),
            asset=first_event.get("asset_id", "Unknown"),
            summary=_get_trace_summary(events_for_trace),
            source=first_event.get("source", "unknown"),
            event_count=len(events_for_trace),
        ))

    return TracesResponse(
        traces=summaries,
        total=total,
        has_more=offset + limit < total,
    )


@router.get("/traces/{trace_id}", response_model=TraceDetail)
async def get_trace(trace_id: str) -> TraceDetail:
    """
    Get detailed information about a specific trace, including all events.
    """
    events = _read_audit_log()
    traces = _group_by_trace(events)

    if trace_id not in traces:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    events_for_trace = traces[trace_id]
    if not events_for_trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} has no events")

    first_event = events_for_trace[0]

    return TraceDetail(
        trace_id=trace_id,
        time=first_event.get("created_at", ""),
        asset=first_event.get("asset_id", "Unknown"),
        summary=_get_trace_summary(events_for_trace),
        source=first_event.get("source", "unknown"),
        events=[
            TraceEvent(
                event_id=e.get("event_id", ""),
                event_type=e.get("event_type", "Unknown"),
                timestamp=e.get("created_at", ""),
                payload=e.get("payload", {}),
            )
            for e in events_for_trace
        ],
    )


@router.get("/traces/{trace_id}/events", response_model=list[TraceEvent])
async def get_trace_events(trace_id: str) -> list[TraceEvent]:
    """
    Get all events for a specific trace.
    """
    events = _read_audit_log()
    traces = _group_by_trace(events)

    if trace_id not in traces:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    events_for_trace = traces[trace_id]

    return [
        TraceEvent(
            event_id=e.get("event_id", ""),
            event_type=e.get("event_type", "Unknown"),
            timestamp=e.get("created_at", ""),
            payload=e.get("payload", {}),
        )
        for e in events_for_trace
    ]

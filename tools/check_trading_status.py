#!/usr/bin/env python3
"""
Diagnostic script to check if trading system was running 24/7 and analyze trigger conditions.

This script:
1. Checks if the trading worker is running
2. Analyzes audit trail logs to see evaluation history
3. Reports on trigger conditions and why trades didn't execute
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional
import requests

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

AUDIT_TRAIL_FILE = Path("backend/logs/audit_trail.jsonl")
API_BASE_URL = "http://localhost:8000/v1"


def load_audit_events(log_file: Path) -> List[Dict[str, Any]]:
    """Load events from JSONL file."""
    events = []
    if not log_file.exists():
        return events

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                continue

    return events


def check_worker_status() -> Optional[Dict[str, Any]]:
    """Check if trading worker is running via API."""
    try:
        response = requests.get(f"{API_BASE_URL}/trading/worker/status", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        print("⚠️  Cannot connect to backend API. Is the backend running?")
    except Exception as e:
        print(f"⚠️  Error checking worker status: {e}")
    return None


def analyze_audit_trail(events: List[Dict[str, Any]], days: int = 7) -> Dict[str, Any]:
    """Analyze audit trail for trading activity."""
    cutoff_date = datetime.now() - timedelta(days=days)

    # Filter events from last N days
    recent_events = [
        e
        for e in events
        if datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")) >= cutoff_date
    ]

    if not recent_events:
        return {"has_recent_activity": False, "message": f"No events found in the last {days} days"}

    # Group by position and event type
    position_stats = defaultdict(
        lambda: {
            "price_events": [],
            "trigger_evaluations": [],
            "guardrail_evaluations": [],
            "orders_created": [],
            "trades_executed": [],
            "first_seen": None,
            "last_seen": None,
        }
    )

    for event in recent_events:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        position_id = payload.get("position_id")
        created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))

        if not position_id:
            continue

        stats = position_stats[position_id]

        if stats["first_seen"] is None or created_at < stats["first_seen"]:
            stats["first_seen"] = created_at
        if stats["last_seen"] is None or created_at > stats["last_seen"]:
            stats["last_seen"] = created_at

        if event_type == "PriceEvent":
            stats["price_events"].append(
                {
                    "timestamp": created_at,
                    "price": float(payload.get("price", 0)),
                    "anchor_price": float(payload.get("anchor_price", 0))
                    if payload.get("anchor_price")
                    else None,
                    "ticker": payload.get("ticker"),
                }
            )
        elif event_type == "TriggerEvaluated":
            trigger_decision = payload.get("trigger_decision", {})
            stats["trigger_evaluations"].append(
                {
                    "timestamp": created_at,
                    "fired": trigger_decision.get("fired", False),
                    "direction": trigger_decision.get("direction"),
                    "reason": trigger_decision.get("reason"),
                    "anchor_price": float(payload.get("anchor_price", 0))
                    if payload.get("anchor_price")
                    else None,
                    "current_price": float(payload.get("current_price", 0))
                    if payload.get("current_price")
                    else None,
                    "threshold_pct": float(payload.get("threshold_pct", 0))
                    if payload.get("threshold_pct")
                    else None,
                    "ticker": payload.get("ticker"),
                }
            )
        elif event_type == "GuardrailEvaluated":
            decision = payload.get("decision", {})
            stats["guardrail_evaluations"].append(
                {
                    "timestamp": created_at,
                    "allowed": decision.get("allowed", False),
                    "reason": decision.get("reason"),
                }
            )
        elif event_type == "OrderCreated":
            stats["orders_created"].append(
                {
                    "timestamp": created_at,
                    "order_id": payload.get("order_id"),
                }
            )
        elif event_type == "ExecutionRecorded":
            stats["trades_executed"].append(
                {
                    "timestamp": created_at,
                    "trade_id": payload.get("trade_id"),
                }
            )

    # Analyze each position
    analysis = {
        "has_recent_activity": True,
        "analysis_period_days": days,
        "total_events": len(recent_events),
        "positions": {},
    }

    for position_id, stats in position_stats.items():
        # Get ticker from first price event
        ticker = stats["price_events"][0]["ticker"] if stats["price_events"] else "UNKNOWN"

        # Calculate time span
        time_span = None
        if stats["first_seen"] and stats["last_seen"]:
            time_span = stats["last_seen"] - stats["first_seen"]

        # Analyze trigger evaluations
        total_checks = len(stats["trigger_evaluations"])
        triggered_count = sum(1 for e in stats["trigger_evaluations"] if e["fired"])

        # Get latest trigger evaluation for details
        latest_trigger = stats["trigger_evaluations"][-1] if stats["trigger_evaluations"] else None

        # Get price range
        prices = [e["price"] for e in stats["price_events"] if e["price"] > 0]
        price_min = min(prices) if prices else None
        price_max = max(prices) if prices else None

        # Get anchor price (should be consistent)
        anchor_prices = [e["anchor_price"] for e in stats["price_events"] if e["anchor_price"]]
        anchor_price = anchor_prices[0] if anchor_prices else None

        # Calculate price deviation from anchor
        price_deviation_pct = None
        if latest_trigger and latest_trigger["anchor_price"] and latest_trigger["current_price"]:
            price_deviation_pct = (
                (latest_trigger["current_price"] - latest_trigger["anchor_price"])
                / latest_trigger["anchor_price"]
                * 100
            )

        analysis["positions"][position_id] = {
            "ticker": ticker,
            "time_span": str(time_span) if time_span else None,
            "first_seen": stats["first_seen"].isoformat() if stats["first_seen"] else None,
            "last_seen": stats["last_seen"].isoformat() if stats["last_seen"] else None,
            "total_checks": total_checks,
            "triggered_count": triggered_count,
            "orders_created": len(stats["orders_created"]),
            "trades_executed": len(stats["trades_executed"]),
            "anchor_price": anchor_price,
            "price_range": {
                "min": price_min,
                "max": price_max,
                "current": latest_trigger["current_price"] if latest_trigger else None,
            },
            "latest_trigger": {
                "fired": latest_trigger["fired"] if latest_trigger else None,
                "reason": latest_trigger["reason"] if latest_trigger else None,
                "threshold_pct": latest_trigger["threshold_pct"] if latest_trigger else None,
                "price_deviation_pct": price_deviation_pct,
            }
            if latest_trigger
            else None,
        }

    return analysis


def print_report(worker_status: Optional[Dict], analysis: Dict[str, Any]):
    """Print diagnostic report."""
    import sys

    # Set UTF-8 encoding for Windows
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("=" * 80)
    print("TRADING SYSTEM DIAGNOSTIC REPORT")
    print("=" * 80)
    print()

    # Worker Status
    print("[WORKER] TRADING WORKER STATUS")
    print("-" * 80)
    if worker_status:
        running = "YES" if worker_status.get("running") else "NO"
        enabled = "YES" if worker_status.get("enabled") else "NO"
        print(f"  Running: {running}")
        print(f"  Enabled: {enabled}")
        print(f"  Interval: {worker_status.get('interval_seconds', 'N/A')} seconds")
    else:
        print("  WARNING: Could not check worker status (backend may not be running)")
    print()

    # Audit Trail Analysis
    print("[AUDIT] AUDIT TRAIL ANALYSIS")
    print("-" * 80)

    if not analysis.get("has_recent_activity"):
        print(f"  ERROR: {analysis.get('message', 'No recent activity')}")
        print()
        return

    print(f"  Analysis Period: Last {analysis['analysis_period_days']} days")
    print(f"  Total Events: {analysis['total_events']}")
    print()

    # Position Details
    for position_id, pos_data in analysis["positions"].items():
        print(f"  Position: {pos_data['ticker']} ({position_id})")
        print(f"    Time Span: {pos_data['time_span'] or 'N/A'}")
        print(f"    First Seen: {pos_data['first_seen'] or 'N/A'}")
        print(f"    Last Seen: {pos_data['last_seen'] or 'N/A'}")
        print(f"    Total Checks: {pos_data['total_checks']}")
        print(f"    Triggers Fired: {pos_data['triggered_count']} / {pos_data['total_checks']}")
        print(f"    Orders Created: {pos_data['orders_created']}")
        print(f"    Trades Executed: {pos_data['trades_executed']}")

        if pos_data.get("anchor_price"):
            print(f"    Anchor Price: ${pos_data['anchor_price']:.2f}")

        if pos_data.get("price_range"):
            pr = pos_data["price_range"]
            print(f"    Price Range: ${pr['min']:.2f} - ${pr['max']:.2f}")
            if pr.get("current"):
                print(f"    Current Price: ${pr['current']:.2f}")

        if pos_data.get("latest_trigger"):
            lt = pos_data["latest_trigger"]
            print("    Latest Trigger Check:")
            fired_status = "YES" if lt["fired"] else "NO"
            print(f"      Fired: {fired_status}")
            print(f"      Reason: {lt['reason'] or 'N/A'}")
            if lt.get("threshold_pct"):
                print(f"      Threshold: +/-{lt['threshold_pct']}%")
            if lt.get("price_deviation_pct") is not None:
                print(f"      Price Deviation: {lt['price_deviation_pct']:.2f}%")
                if abs(lt["price_deviation_pct"]) < lt.get("threshold_pct", 0):
                    print(
                        f"      WARNING: Price movement ({abs(lt['price_deviation_pct']):.2f}%) is below threshold ({lt['threshold_pct']}%)"
                    )

        print()

    # Summary
    print("[SUMMARY]")
    print("-" * 80)
    total_positions = len(analysis["positions"])
    positions_with_trades = sum(
        1 for p in analysis["positions"].values() if p["trades_executed"] > 0
    )

    print(f"  Total Positions Monitored: {total_positions}")
    print(f"  Positions with Trades: {positions_with_trades}")

    if positions_with_trades == 0:
        print()
        print("  WARNING: NO TRADES EXECUTED")
        print("  Possible reasons:")
        print("    1. Price movements were below trigger thresholds (+/-3% by default)")
        print("    2. Guardrails blocked trades (asset % out of bounds)")
        print("    3. Market hours policy prevented after-hours trading")
        print("    4. Insufficient cash/shares for trade")
        print("    5. Order size below minimum notional")
    print()
    print("=" * 80)


def main():
    """Main entry point."""
    # Check worker status
    worker_status = check_worker_status()

    # Analyze audit trail
    events = load_audit_events(AUDIT_TRAIL_FILE)
    analysis = analyze_audit_trail(events, days=7)

    # Print report
    print_report(worker_status, analysis)


if __name__ == "__main__":
    main()

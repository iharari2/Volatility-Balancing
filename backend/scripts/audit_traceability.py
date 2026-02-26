#!/usr/bin/env python3
"""
Traceability Audit Tool
=======================
Verifies that the four overlapping audit stores are mutually consistent:
  - position_evaluation_timeline  (one row per cycle)
  - orders                        (full order lifecycle)
  - trades                        (immutable fill records)
  - events                        (loose audit log)

Usage:
  python scripts/audit_traceability.py [--position-id ID] [--limit N] [--mode LIVE|SIMULATION]

Env:
  SQL_URL  (default: sqlite:///./vb.sqlite, resolved relative to backend/)

Exit codes:
  0  No issues found
  1  One or more gap lists are non-empty
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AuditResult:
    summary: dict = field(default_factory=dict)
    gap1: list[dict] = field(default_factory=list)           # BUY/SELL with no order_id
    gap2_orders: list[dict] = field(default_factory=list)    # dangling order_id refs
    gap2_trades: list[dict] = field(default_factory=list)    # dangling trade_id refs
    gap3_unfilled: list[dict] = field(default_factory=list)  # filled orders without trade
    gap3_stuck: list[dict] = field(default_factory=list)     # submitted orders >5 min, no trade
    gap3_qty_mismatch: list[dict] = field(default_factory=list)
    gap3_cash_mismatch: list[dict] = field(default_factory=list)
    gap4: list[dict] = field(default_factory=list)           # HOLD/SKIP with order_id
    traceability: list[dict] = field(default_factory=list)   # BUY/SELL rows with joins

    @property
    def total_issues(self) -> int:
        return (
            len(self.gap1)
            + len(self.gap2_orders)
            + len(self.gap2_trades)
            + len(self.gap3_unfilled)
            + len(self.gap3_stuck)
            + len(self.gap3_qty_mismatch)
            + len(self.gap3_cash_mismatch)
            + len(self.gap4)
        )

    @property
    def is_clean(self) -> bool:
        return self.total_issues == 0


# ---------------------------------------------------------------------------
# Core audit logic
# ---------------------------------------------------------------------------

def _rows(conn, sql: str, params: dict | None = None) -> list[dict]:
    """Execute a SQL query and return rows as list of dicts."""
    result = conn.execute(text(sql), params or {})
    keys = list(result.keys())
    return [dict(zip(keys, row)) for row in result.fetchall()]


def _check_table_exists(conn, table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        rows = _rows(conn, f"SELECT 1 FROM {table_name} LIMIT 1")
        return True
    except Exception:
        return False


def run_audit(
    engine: Engine,
    position_id: Optional[str] = None,
    limit: int = 1000,
    mode: str = "LIVE",
) -> AuditResult:
    """
    Pure function — takes SQLAlchemy engine, returns structured result.

    All queries use sqlalchemy.text() with bound parameters.
    Works with both SQLite and PostgreSQL.
    """
    result = AuditResult()

    with engine.connect() as conn:
        # ── Build common WHERE clauses ───────────────────────────────────────
        # `where_clause`        — for queries on timeline table only (no alias)
        # `where_clause_t`      — for JOIN queries where timeline is aliased `t`
        timeline_filters = ["mode = :mode"]
        timeline_filters_t = ["t.mode = :mode"]
        params: dict[str, Any] = {"mode": mode, "limit": limit}

        if position_id:
            timeline_filters.append("position_id = :position_id")
            timeline_filters_t.append("t.position_id = :position_id")
            params["position_id"] = position_id

        where_clause = " AND ".join(timeline_filters)
        where_clause_t = " AND ".join(timeline_filters_t)

        # ── Baseline counts ──────────────────────────────────────────────────
        total_rows = _rows(
            conn,
            f"SELECT COUNT(*) AS cnt FROM position_evaluation_timeline WHERE {where_clause}",
            params,
        )[0]["cnt"]

        action_rows = _rows(
            conn,
            f"""
            SELECT COUNT(*) AS cnt
            FROM position_evaluation_timeline
            WHERE {where_clause}
              AND action IN ('BUY', 'SELL')
            """,
            params,
        )[0]["cnt"]

        hold_skip_rows = _rows(
            conn,
            f"""
            SELECT COUNT(*) AS cnt
            FROM position_evaluation_timeline
            WHERE {where_clause}
              AND action IN ('HOLD', 'SKIP')
            """,
            params,
        )[0]["cnt"]

        # Count orders + trades scoped to position if given
        order_params: dict[str, Any] = {}
        order_filter = "1=1"
        order_filter_aliased = "1=1"  # same filter but with table alias prefix for JOINs
        if position_id:
            order_params["position_id"] = position_id
            order_filter = "position_id = :position_id"
            order_filter_aliased = "o.position_id = :position_id"

        total_orders = _rows(
            conn,
            f"SELECT COUNT(*) AS cnt FROM orders WHERE {order_filter}",
            order_params,
        )[0]["cnt"]

        total_trades = _rows(
            conn,
            f"SELECT COUNT(*) AS cnt FROM trades WHERE {order_filter}",
            order_params,
        )[0]["cnt"]

        result.summary = {
            "total_eval_rows": total_rows,
            "action_rows": action_rows,
            "hold_skip_rows": hold_skip_rows,
            "total_orders": total_orders,
            "total_trades": total_trades,
        }

        # ── GAP-1: BUY/SELL rows with no order_id ───────────────────────────
        result.gap1 = _rows(
            conn,
            f"""
            SELECT id, timestamp, position_id, action, action_reason
            FROM position_evaluation_timeline
            WHERE {where_clause}
              AND action IN ('BUY', 'SELL')
              AND (order_id IS NULL OR order_id = '')
            ORDER BY timestamp
            LIMIT :limit
            """,
            params,
        )

        # ── GAP-2: Dangling cross-table references ───────────────────────────
        # 2a: order_id in timeline not in orders table
        result.gap2_orders = _rows(
            conn,
            f"""
            SELECT t.id AS timeline_id, t.timestamp, t.position_id,
                   t.action, t.order_id
            FROM position_evaluation_timeline t
            WHERE {where_clause_t}
              AND t.order_id IS NOT NULL
              AND t.order_id != ''
              AND NOT EXISTS (
                  SELECT 1 FROM orders o WHERE o.id = t.order_id
              )
            ORDER BY t.timestamp
            LIMIT :limit
            """,
            params,
        )

        # 2b: trade_id in timeline not in trades table
        result.gap2_trades = _rows(
            conn,
            f"""
            SELECT t.id AS timeline_id, t.timestamp, t.position_id,
                   t.action, t.trade_id
            FROM position_evaluation_timeline t
            WHERE {where_clause_t}
              AND t.trade_id IS NOT NULL
              AND t.trade_id != ''
              AND NOT EXISTS (
                  SELECT 1 FROM trades tr WHERE tr.id = t.trade_id
              )
            ORDER BY t.timestamp
            LIMIT :limit
            """,
            params,
        )

        # ── GAP-3: Order/Trade gaps + math ──────────────────────────────────
        # 3a: Orders with status='filled' that have no trade row
        result.gap3_unfilled = _rows(
            conn,
            f"""
            SELECT o.id AS order_id, o.position_id, o.side,
                   o.qty, o.status, o.created_at
            FROM orders o
            WHERE {order_filter}
              AND o.status = 'filled'
              AND NOT EXISTS (
                  SELECT 1 FROM trades tr WHERE tr.order_id = o.id
              )
            ORDER BY o.created_at
            LIMIT :limit
            """,
            {**order_params, "limit": limit},
        )

        # 3b: Orders with status='submitted' older than 5 minutes with no trade
        five_min_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        stuck_params = {**order_params, "limit": limit, "cutoff": five_min_ago}
        result.gap3_stuck = _rows(
            conn,
            f"""
            SELECT o.id AS order_id, o.position_id, o.side,
                   o.qty, o.status, o.created_at
            FROM orders o
            WHERE {order_filter}
              AND o.status = 'submitted'
              AND o.created_at < :cutoff
              AND NOT EXISTS (
                  SELECT 1 FROM trades tr WHERE tr.order_id = o.id
              )
            ORDER BY o.created_at
            LIMIT :limit
            """,
            stuck_params,
        )

        # 3c: Qty mismatch between order and trade
        result.gap3_qty_mismatch = _rows(
            conn,
            f"""
            SELECT o.id AS order_id, o.position_id, o.side,
                   o.qty AS order_qty, tr.qty AS trade_qty,
                   ABS(o.qty - tr.qty) AS qty_diff
            FROM orders o
            JOIN trades tr ON tr.order_id = o.id
            WHERE ({order_filter_aliased})
              AND ABS(o.qty - tr.qty) > 0.001
            ORDER BY qty_diff DESC
            LIMIT :limit
            """,
            {**order_params, "limit": limit},
        )

        # 3d: Cash delta mismatch per timeline row
        # cash_delta actual = position_cash_after - position_cash_before
        # cash_delta expected:
        #   BUY:  -(qty * price) - commission  (cost + commission)
        #   SELL: +(qty * price) - commission  (proceeds - commission)
        # Tolerance: ±$0.01
        result.gap3_cash_mismatch = _rows(
            conn,
            f"""
            SELECT
                t.id AS timeline_id,
                t.timestamp,
                t.position_id,
                t.action,
                t.position_cash_before,
                t.position_cash_after,
                t.execution_qty,
                t.execution_price,
                t.execution_commission,
                (t.position_cash_after - t.position_cash_before) AS actual_delta,
                CASE
                    WHEN t.action = 'BUY'
                        THEN -(t.execution_qty * t.execution_price) - t.execution_commission
                    WHEN t.action = 'SELL'
                        THEN (t.execution_qty * t.execution_price) - t.execution_commission
                END AS expected_delta
            FROM position_evaluation_timeline t
            WHERE {where_clause_t}
              AND t.action IN ('BUY', 'SELL')
              AND t.position_cash_before IS NOT NULL
              AND t.position_cash_after IS NOT NULL
              AND t.execution_qty IS NOT NULL
              AND t.execution_price IS NOT NULL
              AND t.execution_commission IS NOT NULL
              AND ABS(
                    (t.position_cash_after - t.position_cash_before)
                    - CASE
                        WHEN t.action = 'BUY'
                            THEN -(t.execution_qty * t.execution_price) - t.execution_commission
                        WHEN t.action = 'SELL'
                            THEN (t.execution_qty * t.execution_price) - t.execution_commission
                      END
                  ) > 0.01
            ORDER BY t.timestamp
            LIMIT :limit
            """,
            params,
        )

        # ── GAP-4: HOLD/SKIP rows that have an order_id ──────────────────────
        result.gap4 = _rows(
            conn,
            f"""
            SELECT id, timestamp, position_id, action, order_id
            FROM position_evaluation_timeline
            WHERE {where_clause}
              AND action IN ('HOLD', 'SKIP')
              AND order_id IS NOT NULL
              AND order_id != ''
            ORDER BY timestamp
            LIMIT :limit
            """,
            params,
        )

        # ── Traceability table (informational) ───────────────────────────────
        result.traceability = _rows(
            conn,
            f"""
            SELECT
                t.timestamp,
                t.position_id,
                t.action,
                t.order_id,
                o.status  AS order_status,
                t.trade_id,
                tr.qty    AS trade_qty,
                tr.price  AS trade_price
            FROM position_evaluation_timeline t
            LEFT JOIN orders o  ON o.id  = t.order_id
            LEFT JOIN trades tr ON tr.id = t.trade_id
            WHERE {where_clause_t}
              AND t.action IN ('BUY', 'SELL')
            ORDER BY t.timestamp
            LIMIT :limit
            """,
            params,
        )

    return result


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_report(result: AuditResult, db_url: str = "", scope: str = "") -> str:
    lines: list[str] = []

    def h1(text: str) -> None:
        lines.append(f"══ {text} {'═' * max(0, 60 - len(text))}")

    def h2(label: str, count: int) -> None:
        lines.append(f"\n── {label}  ({count} issues) {'─' * max(0, 40 - len(label))}")

    def ok(msg: str) -> None:
        lines.append(f"  ✓ {msg}")

    def issue(row: dict, fields: list[str]) -> None:
        parts = "  |  ".join(f"{k}={row.get(k, '-')}" for k in fields)
        lines.append(f"  ✗ {parts}")

    s = result.summary
    status = "✓ CLEAN" if result.is_clean else f"✗ {result.total_issues} ISSUE(S)"

    h1("Traceability Audit")
    if db_url:
        lines.append(f"  DB    : {db_url}")
    if scope:
        lines.append(f"  Scope : {scope}")
    lines.append(
        f"  Rows  : {s.get('total_eval_rows', 0)} eval rows"
        f"  ({s.get('action_rows', 0)} BUY/SELL,"
        f"  {s.get('hold_skip_rows', 0)} HOLD/SKIP)"
    )
    lines.append(
        f"  Orders: {s.get('total_orders', 0)}"
        f"  |  Trades: {s.get('total_trades', 0)}"
        f"  |  Issues: {result.total_issues}  {status}"
    )

    # GAP-1
    h2("GAP-1  BUY/SELL with no order_id", len(result.gap1))
    if result.gap1:
        for row in result.gap1:
            issue(row, ["timestamp", "position_id", "action", "action_reason"])
    else:
        ok("All BUY/SELL rows have an order_id.")

    # GAP-2
    h2("GAP-2  Dangling references", len(result.gap2_orders) + len(result.gap2_trades))
    if result.gap2_orders:
        lines.append("  [order_id refs not in orders table]")
        for row in result.gap2_orders:
            issue(row, ["timeline_id", "timestamp", "position_id", "order_id"])
    if result.gap2_trades:
        lines.append("  [trade_id refs not in trades table]")
        for row in result.gap2_trades:
            issue(row, ["timeline_id", "timestamp", "position_id", "trade_id"])
    if not result.gap2_orders and not result.gap2_trades:
        ok("All order_id / trade_id references resolve.")

    # GAP-3
    gap3_count = (
        len(result.gap3_unfilled)
        + len(result.gap3_stuck)
        + len(result.gap3_qty_mismatch)
        + len(result.gap3_cash_mismatch)
    )
    h2("GAP-3  Order/trade gaps + math", gap3_count)
    if result.gap3_unfilled:
        lines.append("  [filled orders with no trade]")
        for row in result.gap3_unfilled:
            issue(row, ["order_id", "position_id", "side", "qty", "created_at"])
    if result.gap3_stuck:
        lines.append("  [submitted orders >5 min with no trade]")
        for row in result.gap3_stuck:
            issue(row, ["order_id", "position_id", "side", "qty", "created_at"])
    if result.gap3_qty_mismatch:
        lines.append("  [qty mismatch between order and trade]")
        for row in result.gap3_qty_mismatch:
            issue(row, ["order_id", "position_id", "order_qty", "trade_qty", "qty_diff"])
    if result.gap3_cash_mismatch:
        lines.append("  [cash delta mismatch (tolerance ±$0.01)]")
        for row in result.gap3_cash_mismatch:
            issue(row, ["timeline_id", "timestamp", "action", "actual_delta", "expected_delta"])
    if gap3_count == 0:
        ok("All filled orders have trades. Qty and cash match.")

    # GAP-4
    h2("GAP-4  HOLD/SKIP cleanliness", len(result.gap4))
    if result.gap4:
        for row in result.gap4:
            issue(row, ["timestamp", "position_id", "action", "order_id"])
    else:
        ok("No HOLD/SKIP rows carry an order_id.")

    # Traceability table
    lines.append(f"\n── Traceability Table  (BUY/SELL rows) {'─' * 25}")
    if result.traceability:
        header = (
            f"  {'TIMESTAMP':<20}  {'POSITION':<12}  {'ACT':<5}  "
            f"{'ORDER_ID':<12}  {'ORD_ST':<10}  "
            f"{'TRADE_ID':<12}  {'QTY':>8}  {'PRICE':>8}  ST"
        )
        lines.append(header)
        lines.append("  " + "-" * (len(header) - 2))
        for row in result.traceability:
            ts = str(row.get("timestamp", ""))[:19]
            pos = str(row.get("position_id", ""))[:12]
            act = str(row.get("action", ""))[:5]
            oid = str(row.get("order_id") or "")[:12]
            ost = str(row.get("order_status") or "")[:10]
            tid = str(row.get("trade_id") or "")[:12]
            qty = row.get("trade_qty")
            prc = row.get("trade_price")
            qty_s = f"{qty:>8.4f}" if qty is not None else f"{'—':>8}"
            prc_s = f"{prc:>8.2f}" if prc is not None else f"{'—':>8}"

            # Status indicator
            if oid and ost in ("filled", "executed"):
                st = "✓"
            elif oid:
                st = "~"
            else:
                st = "✗"

            lines.append(
                f"  {ts:<20}  {pos:<12}  {act:<5}  "
                f"{oid:<12}  {ost:<10}  "
                f"{tid:<12}  {qty_s}  {prc_s}  {st}"
            )
    else:
        lines.append("  (no BUY/SELL rows in scope)")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _resolve_sql_url(url: str) -> str:
    """Resolve relative SQLite URLs relative to the backend/ directory."""
    if not url.startswith("sqlite:///./"):
        return url
    rel_path = url[len("sqlite:///./"):]
    # Resolve relative to the directory containing this script's parent (backend/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)  # scripts/ → backend/
    abs_path = os.path.join(backend_dir, rel_path)
    return f"sqlite:///{abs_path}"


def main() -> None:
    # Ensure Unicode output works on all platforms (including Windows cp1252 consoles)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Volatility-Balancing traceability audit tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--position-id", help="Scope audit to a single position ID")
    parser.add_argument("--limit", type=int, default=1000, help="Max rows per check (default 1000)")
    parser.add_argument(
        "--mode",
        default="LIVE",
        choices=["LIVE", "SIMULATION"],
        help="Evaluation mode filter (default LIVE)",
    )
    args = parser.parse_args()

    sql_url_raw = os.getenv("SQL_URL", "sqlite:///./vb.sqlite")
    sql_url = _resolve_sql_url(sql_url_raw)

    scope_parts = []
    if args.position_id:
        scope_parts.append(f"position={args.position_id}")
    else:
        scope_parts.append("ALL positions")
    scope_parts.append(f"mode={args.mode}")
    scope_parts.append(f"limit={args.limit}")
    scope = "  |  ".join(scope_parts)

    engine = create_engine(sql_url, future=True)
    result = run_audit(engine, position_id=args.position_id, limit=args.limit, mode=args.mode)
    report = format_report(result, db_url=sql_url_raw, scope=scope)
    print(report)

    sys.exit(0 if result.is_clean else 1)


if __name__ == "__main__":
    main()

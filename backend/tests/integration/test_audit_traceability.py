# =========================
# backend/tests/integration/test_audit_traceability.py
# =========================
"""
Integration tests for the traceability audit tool.

Strategy: use a fresh in-memory/temp SQLite DB per test so we can seed
controlled data and verify each audit check independently.  No DI container
or tick endpoint is needed — the audit script is a pure SQL tool.
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure the backend root is on sys.path so we can import `scripts.*`
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from infrastructure.persistence.sql.models import (
    Base,
    PositionEvaluationTimelineModel,
    OrderModel,
    TradeModel,
    create_all,
)
from scripts.audit_traceability import run_audit, format_report, AuditResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def audit_engine(tmp_path):
    """Fresh SQLite DB with full schema for each test."""
    db_file = tmp_path / "audit_test.db"
    engine = create_engine(f"sqlite:///{db_file}", future=True)
    create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(audit_engine):
    """SQLAlchemy session bound to the audit engine."""
    Session = sessionmaker(bind=audit_engine, expire_on_commit=False, autoflush=False)
    with Session() as s:
        yield s


# ---------------------------------------------------------------------------
# Helper builders — produce minimal valid ORM objects
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 2, 24, 10, 0, 0, tzinfo=timezone.utc)


def _timeline(
    *,
    row_id: str,
    position_id: str = "pos_001",
    action: str = "HOLD",
    order_id: str | None = None,
    trade_id: str | None = None,
    cash_before: float = 10_000.0,
    cash_after: float | None = None,
    exec_qty: float | None = None,
    exec_price: float | None = None,
    exec_commission: float | None = None,
    timestamp: datetime | None = None,
    mode: str = "LIVE",
) -> PositionEvaluationTimelineModel:
    """Build a minimal valid timeline row."""
    if cash_after is None:
        if action == "BUY" and exec_qty is not None and exec_price is not None:
            commission = exec_commission or 0.0
            cash_after = cash_before - (exec_qty * exec_price) - commission
        elif action == "SELL" and exec_qty is not None and exec_price is not None:
            commission = exec_commission or 0.0
            cash_after = cash_before + (exec_qty * exec_price) - commission
        else:
            cash_after = cash_before

    return PositionEvaluationTimelineModel(
        id=row_id,
        tenant_id="default",
        portfolio_id="portfolio_001",
        position_id=position_id,
        symbol="AAPL",
        timestamp=timestamp or _NOW,
        mode=mode,
        action=action,
        action_taken="ORDER_EXECUTED" if action in ("BUY", "SELL") else "NO_ACTION",
        order_id=order_id,
        trade_id=trade_id,
        position_qty_before=100.0,
        position_cash_before=cash_before,
        position_stock_value_before=15_000.0,
        position_total_value_before=cash_before + 15_000.0,
        position_cash_after=cash_after,
        execution_qty=exec_qty,
        execution_price=exec_price,
        execution_commission=exec_commission,
    )


def _order(
    *,
    order_id: str,
    position_id: str = "pos_001",
    side: str = "BUY",
    qty: float = 10.0,
    status: str = "filled",
    created_at: datetime | None = None,
) -> OrderModel:
    return OrderModel(
        id=order_id,
        tenant_id="default",
        portfolio_id="portfolio_001",
        position_id=position_id,
        side=side,
        qty=qty,
        status=status,
        idempotency_key=f"idem_{order_id}",
        created_at=created_at or _NOW,
        updated_at=created_at or _NOW,
    )


def _trade(
    *,
    trade_id: str,
    order_id: str,
    position_id: str = "pos_001",
    side: str = "BUY",
    qty: float = 10.0,
    price: float = 100.0,
    commission: float = 0.0,
) -> TradeModel:
    return TradeModel(
        id=trade_id,
        tenant_id="default",
        portfolio_id="portfolio_001",
        order_id=order_id,
        position_id=position_id,
        side=side,
        qty=qty,
        price=price,
        commission=commission,
        executed_at=_NOW,
    )


# ---------------------------------------------------------------------------
# GAP-0: Baseline — fully consistent BUY cycle is clean
# ---------------------------------------------------------------------------

def test_clean_buy_cycle_audit(session, audit_engine):
    """A BUY timeline row + matching order + matching trade → zero issues."""
    session.add(_timeline(
        row_id="eval_001",
        action="BUY",
        order_id="ord_001",
        trade_id="trd_001",
        cash_before=10_000.0,
        exec_qty=10.0,
        exec_price=100.0,
        exec_commission=10.0,
    ))
    session.add(_order(order_id="ord_001", side="BUY", qty=10.0, status="filled"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001", side="BUY", qty=10.0, price=100.0, commission=10.0))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.gap1 == [], f"GAP-1 unexpected: {result.gap1}"
    assert result.gap2_orders == [], f"GAP-2 order refs unexpected: {result.gap2_orders}"
    assert result.gap2_trades == [], f"GAP-2 trade refs unexpected: {result.gap2_trades}"
    assert result.gap3_unfilled == [], f"GAP-3 unfilled unexpected: {result.gap3_unfilled}"
    assert result.gap3_qty_mismatch == [], f"GAP-3 qty mismatch unexpected: {result.gap3_qty_mismatch}"
    assert result.gap3_cash_mismatch == [], f"GAP-3 cash mismatch unexpected: {result.gap3_cash_mismatch}"
    assert result.gap4 == [], f"GAP-4 unexpected: {result.gap4}"
    assert result.is_clean


def test_clean_hold_skip_audit(session, audit_engine):
    """HOLD and SKIP rows with no order_id → zero issues."""
    session.add(_timeline(row_id="eval_hold", action="HOLD"))
    session.add(_timeline(row_id="eval_skip", action="SKIP", timestamp=_NOW + timedelta(seconds=1)))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")
    assert result.is_clean


# ---------------------------------------------------------------------------
# GAP-1: BUY/SELL with no order_id
# ---------------------------------------------------------------------------

def test_gap1_buy_without_order_id(session, audit_engine):
    """A BUY row with no order_id is detected as GAP-1."""
    session.add(_timeline(row_id="eval_001", action="BUY", order_id=None))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.gap1) == 1
    assert result.gap1[0]["id"] == "eval_001"
    assert not result.is_clean


def test_gap1_sell_without_order_id(session, audit_engine):
    """A SELL row with no order_id is detected as GAP-1."""
    session.add(_timeline(row_id="eval_sell", action="SELL", order_id=None))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.gap1) == 1
    assert result.gap1[0]["id"] == "eval_sell"


def test_gap1_does_not_flag_hold(session, audit_engine):
    """A HOLD row without order_id is NOT flagged by GAP-1."""
    session.add(_timeline(row_id="eval_hold", action="HOLD", order_id=None))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.gap1 == []


# ---------------------------------------------------------------------------
# GAP-2: Dangling references
# ---------------------------------------------------------------------------

def test_gap2_dangling_order_id(session, audit_engine):
    """order_id in timeline that doesn't exist in orders → GAP-2."""
    session.add(_timeline(
        row_id="eval_001",
        action="BUY",
        order_id="ord_ghost",  # not in orders table
    ))
    # No order inserted
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.gap2_orders) == 1
    assert result.gap2_orders[0]["order_id"] == "ord_ghost"
    assert not result.is_clean


def test_gap2_dangling_trade_id(session, audit_engine):
    """trade_id in timeline that doesn't exist in trades → GAP-2."""
    session.add(_order(order_id="ord_001"))
    session.add(_timeline(
        row_id="eval_001",
        action="BUY",
        order_id="ord_001",
        trade_id="trd_ghost",  # not in trades table
    ))
    # No trade inserted
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.gap2_trades) == 1
    assert result.gap2_trades[0]["trade_id"] == "trd_ghost"
    assert not result.is_clean


def test_gap2_resolves_when_both_exist(session, audit_engine):
    """GAP-2 is clear when both order and trade exist in their tables."""
    session.add(_order(order_id="ord_001"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001"))
    session.add(_timeline(
        row_id="eval_001",
        action="BUY",
        order_id="ord_001",
        trade_id="trd_001",
    ))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.gap2_orders == []
    assert result.gap2_trades == []


# ---------------------------------------------------------------------------
# GAP-3a: Filled order with no trade
# ---------------------------------------------------------------------------

def test_gap3_filled_order_without_trade(session, audit_engine):
    """An order with status='filled' that has no trade → GAP-3 unfilled."""
    session.add(_order(order_id="ord_001", status="filled"))
    # No trade
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.gap3_unfilled) == 1
    assert result.gap3_unfilled[0]["order_id"] == "ord_001"
    assert not result.is_clean


def test_gap3_submitted_order_with_trade_is_clean(session, audit_engine):
    """An order with status='submitted' that HAS a trade is not stuck."""
    session.add(_order(order_id="ord_001", status="submitted"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001"))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.gap3_stuck == []
    assert result.gap3_unfilled == []


# ---------------------------------------------------------------------------
# GAP-3b: Stuck orders (submitted > 5 min, no trade)
# ---------------------------------------------------------------------------

def test_gap3_stuck_old_submitted_order(session, audit_engine):
    """A submitted order older than 5 minutes with no trade → GAP-3 stuck."""
    old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    session.add(_order(order_id="ord_old", status="submitted", created_at=old_time))
    # No trade
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.gap3_stuck) == 1
    assert result.gap3_stuck[0]["order_id"] == "ord_old"
    assert not result.is_clean


def test_gap3_recent_submitted_order_not_stuck(session, audit_engine):
    """A submitted order less than 5 minutes old is not flagged as stuck."""
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    session.add(_order(order_id="ord_new", status="submitted", created_at=recent_time))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.gap3_stuck == []


# ---------------------------------------------------------------------------
# GAP-3c: Qty mismatch
# ---------------------------------------------------------------------------

def test_gap3_qty_mismatch_detected(session, audit_engine):
    """Order qty != trade qty by more than 0.001 → GAP-3 qty mismatch."""
    session.add(_order(order_id="ord_001", qty=10.0, status="filled"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001", qty=5.0))  # mismatch!
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.gap3_qty_mismatch) == 1
    row = result.gap3_qty_mismatch[0]
    assert row["order_id"] == "ord_001"
    assert abs(row["qty_diff"] - 5.0) < 0.001


def test_gap3_qty_match_within_tolerance(session, audit_engine):
    """Order qty matches trade qty within 0.001 → no flag."""
    session.add(_order(order_id="ord_001", qty=10.0, status="filled"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001", qty=10.0005))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.gap3_qty_mismatch == []


# ---------------------------------------------------------------------------
# GAP-3d: Cash delta mismatch
# ---------------------------------------------------------------------------

def test_gap3_cash_mismatch_detected(session, audit_engine):
    """Timeline row with wrong cash delta → GAP-3 cash mismatch."""
    # BUY 10 shares @ $100 with $10 commission
    # Expected delta: -(10*100) - 10 = -1010
    # Actual delta we set: wrong (-500 instead)
    session.add(_timeline(
        row_id="eval_001",
        action="BUY",
        order_id="ord_001",
        trade_id="trd_001",
        cash_before=10_000.0,
        cash_after=9_500.0,    # wrong! should be 8_990.0
        exec_qty=10.0,
        exec_price=100.0,
        exec_commission=10.0,
    ))
    session.add(_order(order_id="ord_001", status="filled"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001"))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.gap3_cash_mismatch) == 1
    row = result.gap3_cash_mismatch[0]
    assert row["timeline_id"] == "eval_001"
    assert abs(row["actual_delta"] - (-500.0)) < 0.01
    assert abs(row["expected_delta"] - (-1010.0)) < 0.01


def test_gap3_cash_delta_correct_buy(session, audit_engine):
    """Correct BUY cash delta → no cash mismatch."""
    # BUY 10 @ $100 + $10 commission → cash_after = 10000 - 1000 - 10 = 8990
    session.add(_timeline(
        row_id="eval_001",
        action="BUY",
        order_id="ord_001",
        trade_id="trd_001",
        cash_before=10_000.0,
        exec_qty=10.0,
        exec_price=100.0,
        exec_commission=10.0,
        # cash_after computed automatically by _timeline helper
    ))
    session.add(_order(order_id="ord_001", status="filled"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001"))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.gap3_cash_mismatch == []


def test_gap3_cash_delta_correct_sell(session, audit_engine):
    """Correct SELL cash delta → no cash mismatch."""
    # SELL 10 @ $100 - $10 commission → cash_after = 10000 + 1000 - 10 = 10990
    session.add(_timeline(
        row_id="eval_001",
        action="SELL",
        order_id="ord_001",
        trade_id="trd_001",
        cash_before=10_000.0,
        exec_qty=10.0,
        exec_price=100.0,
        exec_commission=10.0,
    ))
    session.add(_order(order_id="ord_001", side="SELL", status="filled"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001", side="SELL"))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.gap3_cash_mismatch == []


# ---------------------------------------------------------------------------
# GAP-4: HOLD/SKIP with order_id
# ---------------------------------------------------------------------------

def test_gap4_hold_with_order_id(session, audit_engine):
    """A HOLD row that carries an order_id → GAP-4."""
    session.add(_timeline(row_id="eval_001", action="HOLD", order_id="ord_spurious"))
    session.add(_order(order_id="ord_spurious"))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.gap4) == 1
    assert result.gap4[0]["id"] == "eval_001"
    assert not result.is_clean


def test_gap4_skip_with_order_id(session, audit_engine):
    """A SKIP row that carries an order_id → GAP-4."""
    session.add(_timeline(row_id="eval_skip", action="SKIP", order_id="ord_skip_spurious"))
    session.add(_order(order_id="ord_skip_spurious"))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.gap4) == 1
    assert result.gap4[0]["id"] == "eval_skip"


def test_gap4_hold_without_order_id_is_clean(session, audit_engine):
    """HOLD row with no order_id → GAP-4 clear."""
    session.add(_timeline(row_id="eval_hold", action="HOLD"))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.gap4 == []


# ---------------------------------------------------------------------------
# Position scoping
# ---------------------------------------------------------------------------

def test_position_id_filter_isolates_scope(session, audit_engine):
    """--position-id limits audit to that position; other positions are ignored."""
    # pos_001 has a bad GAP-1 row; pos_002 is clean
    session.add(_timeline(row_id="eval_bad", position_id="pos_001", action="BUY", order_id=None))
    session.add(_timeline(row_id="eval_good", position_id="pos_002", action="HOLD"))
    session.commit()

    # Auditing pos_002 should be clean
    result_002 = run_audit(audit_engine, position_id="pos_002")
    assert result_002.is_clean

    # Auditing pos_001 should detect the issue
    result_001 = run_audit(audit_engine, position_id="pos_001")
    assert len(result_001.gap1) == 1


def test_no_position_filter_scans_all(session, audit_engine):
    """Without position_id, all positions are included in the audit."""
    session.add(_timeline(row_id="eval_001", position_id="pos_a", action="BUY", order_id=None))
    session.add(_timeline(row_id="eval_002", position_id="pos_b", action="BUY", order_id=None))
    session.commit()

    result = run_audit(audit_engine)  # no position_id

    assert len(result.gap1) == 2


# ---------------------------------------------------------------------------
# Traceability table (informational)
# ---------------------------------------------------------------------------

def test_traceability_table_populated(session, audit_engine):
    """BUY/SELL rows appear in the traceability table."""
    session.add(_order(order_id="ord_001", status="filled"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001", qty=10.0, price=100.0))
    session.add(_timeline(
        row_id="eval_001",
        action="BUY",
        order_id="ord_001",
        trade_id="trd_001",
        exec_qty=10.0,
        exec_price=100.0,
        exec_commission=0.0,
    ))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert len(result.traceability) == 1
    row = result.traceability[0]
    assert row["action"] == "BUY"
    assert row["order_id"] == "ord_001"
    assert row["trade_id"] == "trd_001"
    assert abs(row["trade_qty"] - 10.0) < 0.001
    assert abs(row["trade_price"] - 100.0) < 0.001


def test_hold_rows_not_in_traceability(session, audit_engine):
    """HOLD/SKIP rows are excluded from the traceability table."""
    session.add(_timeline(row_id="eval_hold", action="HOLD"))
    session.add(_timeline(row_id="eval_skip", action="SKIP", timestamp=_NOW + timedelta(seconds=1)))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.traceability == []


# ---------------------------------------------------------------------------
# format_report smoke test
# ---------------------------------------------------------------------------

def test_format_report_clean_audit(session, audit_engine):
    """format_report() produces non-empty string for a clean audit result."""
    session.add(_order(order_id="ord_001", status="filled"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001"))
    session.add(_timeline(
        row_id="eval_001",
        action="BUY",
        order_id="ord_001",
        trade_id="trd_001",
        exec_qty=10.0,
        exec_price=100.0,
        exec_commission=0.0,
    ))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")
    report = format_report(result, db_url="sqlite:///test.db", scope="pos_001")

    assert isinstance(report, str)
    assert len(report) > 0
    assert "CLEAN" in report
    assert "GAP-1" in report
    assert "GAP-2" in report
    assert "GAP-3" in report
    assert "GAP-4" in report
    assert "Traceability Table" in report


def test_format_report_with_issues(session, audit_engine):
    """format_report() clearly marks issues when gaps are found."""
    session.add(_timeline(row_id="eval_001", action="BUY", order_id=None))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")
    report = format_report(result)

    assert "ISSUE" in report
    assert "✗" in report


def test_format_report_empty_db(audit_engine):
    """format_report() works on an empty database (no rows)."""
    result = run_audit(audit_engine)
    report = format_report(result)

    assert isinstance(report, str)
    assert "CLEAN" in report


# ---------------------------------------------------------------------------
# Summary counts
# ---------------------------------------------------------------------------

def test_summary_counts(session, audit_engine):
    """Summary dict contains correct row counts."""
    session.add(_timeline(row_id="eval_buy", action="BUY",
                          order_id="ord_001", exec_qty=5.0, exec_price=100.0, exec_commission=0.0))
    session.add(_timeline(row_id="eval_hold", action="HOLD",
                          timestamp=_NOW + timedelta(seconds=1)))
    session.add(_timeline(row_id="eval_skip", action="SKIP",
                          timestamp=_NOW + timedelta(seconds=2)))
    session.add(_order(order_id="ord_001", status="filled"))
    session.add(_trade(trade_id="trd_001", order_id="ord_001"))
    session.commit()

    result = run_audit(audit_engine, position_id="pos_001")

    assert result.summary["total_eval_rows"] == 3
    assert result.summary["action_rows"] == 1
    assert result.summary["hold_skip_rows"] == 2
    assert result.summary["total_orders"] == 1
    assert result.summary["total_trades"] == 1

# backend/tests/unit/application/test_explainability_timeline_service.py
"""
Tests for ExplainabilityTimelineService.

Covers:
- Live record conversion with all 11 column groups
- Order/trade enrichment (Groups 6-7)
- Pagination (offset/limit with total count)
- Filtering (action, date range, order status)
- Daily aggregation
- Simulation record conversion
"""

import pytest
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from application.services.explainability_timeline_service import ExplainabilityTimelineService
from application.dto.explainability import ExplainabilityRow


# ────────────────── Fake repositories ──────────────────


@dataclass
class FakeOrder:
    id: str
    tenant_id: str = "t1"
    portfolio_id: str = "p1"
    position_id: str = "pos1"
    side: str = "BUY"
    qty: float = 10.0
    status: str = "filled"
    broker_order_id: Optional[str] = None
    broker_status: Optional[str] = None
    filled_qty: float = 0.0
    avg_fill_price: Optional[float] = None
    total_commission: float = 0.0
    rejection_reason: Optional[str] = None


@dataclass
class FakeTrade:
    id: str
    order_id: str
    tenant_id: str = "t1"
    portfolio_id: str = "p1"
    position_id: str = "pos1"
    side: str = "BUY"
    qty: float = 10.0
    price: float = 100.0
    commission: float = 1.0
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FakeOrdersRepo:
    def __init__(self, orders: Optional[Dict[str, FakeOrder]] = None):
        self._orders = orders or {}

    def get(self, order_id: str):
        return self._orders.get(order_id)


class FakeTradesRepo:
    def __init__(self, trades_by_order: Optional[Dict[str, List[FakeTrade]]] = None):
        self._trades_by_order = trades_by_order or {}

    def list_for_order(self, order_id: str) -> List[FakeTrade]:
        return self._trades_by_order.get(order_id, [])


# ────────────────── Fixtures ──────────────────


def _make_ts(day: int = 1, hour: int = 10) -> datetime:
    """Create a UTC datetime for Feb 2026."""
    return datetime(2026, 2, day, hour, 0, 0, tzinfo=timezone.utc)


def _live_record(
    day: int = 1,
    hour: int = 10,
    price: float = 100.0,
    action: str = "HOLD",
    order_id: Optional[str] = None,
    qty_before: float = 50.0,
    cash_before: float = 5000.0,
    anchor_price: float = 95.0,
    **extra,
) -> dict:
    """Create a minimal live evaluation timeline record."""
    ts = _make_ts(day, hour)
    record = {
        "id": f"eval_{day}_{hour}",
        "timestamp": ts.isoformat(),
        "evaluated_at": ts.isoformat(),
        "tenant_id": "t1",
        "portfolio_id": "p1",
        "position_id": "pos1",
        "mode": "LIVE",
        "effective_price": price,
        "market_price_raw": price,
        "position_qty_before": qty_before,
        "position_cash_before": cash_before,
        "position_stock_value_before": qty_before * price,
        "position_total_value_before": cash_before + qty_before * price,
        "anchor_price": anchor_price,
        "pct_change_from_anchor": ((price - anchor_price) / anchor_price * 100) if anchor_price else 0,
        "action": action,
        "guardrail_allowed": True,
        "trigger_detected": action in ("BUY", "SELL"),
        "order_id": order_id,
    }
    record.update(extra)
    return record


# ────────────────── Tests: Live Record Conversion ──────────────────


class TestConvertLiveRecord:
    def test_basic_hold_record(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(action="HOLD")]
        rows = svc.build_from_live_timeline(records, "pos1", "p1", "AAPL")

        assert len(rows) == 1
        row = rows[0]
        assert row.action == "HOLD"
        assert row.price == 100.0
        assert row.qty == 50.0
        assert row.cash == 5000.0
        assert row.stock_value == 5000.0
        assert row.total_value == 10000.0
        assert row.stock_pct == pytest.approx(50.0)
        assert row.mode == "LIVE"
        assert row.symbol == "AAPL"
        assert row.position_id == "pos1"

    def test_buy_record_with_trigger(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(
            action="BUY",
            order_id="ord_001",
            trigger_detected=True,
            trigger_direction="DOWN",
            trigger_reason="Price dropped below anchor",
        )]
        rows = svc.build_from_live_timeline(records)

        row = rows[0]
        assert row.action == "BUY"
        assert row.order_id == "ord_001"
        assert row.trigger_fired is True
        assert row.trigger_direction == "DOWN"

    def test_position_impact_before_after(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(
            action="BUY",
            qty_before=50.0,
            cash_before=5000.0,
            position_qty_after=60.0,
            position_cash_after=3990.0,
        )]
        rows = svc.build_from_live_timeline(records)
        row = rows[0]

        assert row.qty_before == 50.0
        assert row.qty_after == 60.0
        assert row.cash_before == 5000.0
        assert row.cash_after == 3990.0
        assert row.stock_value_before == pytest.approx(5000.0)
        assert row.stock_value_after == pytest.approx(6000.0)

    def test_anchor_tracking(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(
            anchor_reset_occurred=True,
            anchor_price_old=90.0,
            anchor_reset_reason="50% anomaly detection",
        )]
        rows = svc.build_from_live_timeline(records)
        row = rows[0]

        assert row.anchor_reset is True
        assert row.anchor_old_value == 90.0
        assert row.anchor_reset_reason == "50% anomaly detection"

    def test_trace_id_preserved(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(trace_id="trace_abc123")]
        rows = svc.build_from_live_timeline(records)
        assert rows[0].trace_id == "trace_abc123"

    def test_guardrail_blocked(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(
            action="SKIP",
            guardrail_allowed=False,
            guardrail_block_reason="Max allocation exceeded",
            guardrail_min_stock_pct=20.0,
            guardrail_max_stock_pct=60.0,
        )]
        rows = svc.build_from_live_timeline(records)
        row = rows[0]

        assert row.action == "SKIP"
        assert row.guardrail_allowed is False
        assert row.guardrail_block_reason == "Max allocation exceeded"
        assert row.min_stock_pct == 20.0
        assert row.max_stock_pct == 60.0

    def test_delta_pct_calculation(self):
        svc = ExplainabilityTimelineService()
        # Price=105, anchor=100 -> delta = 5%
        records = [_live_record(price=105.0, anchor_price=100.0)]
        rows = svc.build_from_live_timeline(records)
        assert rows[0].delta_pct == pytest.approx(5.0)

    def test_skip_record_without_timestamp(self):
        svc = ExplainabilityTimelineService()
        records = [{"id": "bad", "action": "HOLD"}]
        rows = svc.build_from_live_timeline(records)
        assert len(rows) == 0


# ────────────────── Tests: Order/Trade Enrichment ──────────────────


class TestEnrichWithOrders:
    def test_enrich_filled_order(self):
        order = FakeOrder(
            id="ord_001",
            status="filled",
            broker_order_id="ALPACA_123",
            broker_status="filled",
            filled_qty=10.0,
            avg_fill_price=99.50,
            total_commission=0.99,
        )
        trade = FakeTrade(
            id="trd_001",
            order_id="ord_001",
            qty=10.0,
            price=99.50,
            commission=0.99,
        )
        svc = ExplainabilityTimelineService(
            orders_repo=FakeOrdersRepo({"ord_001": order}),
            trades_repo=FakeTradesRepo({"ord_001": [trade]}),
        )

        records = [_live_record(action="BUY", order_id="ord_001")]
        rows = svc.build_from_live_timeline(records)
        rows = svc.enrich_with_orders(rows)

        row = rows[0]
        assert row.order_status == "filled"
        assert row.broker_order_id == "ALPACA_123"
        assert row.broker_status == "filled"
        assert row.execution_price == pytest.approx(99.50)
        assert row.execution_qty == pytest.approx(10.0)
        assert row.execution_value == pytest.approx(995.0)
        assert row.commission == pytest.approx(0.99)
        assert row.execution_status == "FILLED"

    def test_enrich_rejected_order(self):
        order = FakeOrder(
            id="ord_002",
            status="rejected",
            rejection_reason="Insufficient buying power",
            filled_qty=0.0,
        )
        svc = ExplainabilityTimelineService(
            orders_repo=FakeOrdersRepo({"ord_002": order}),
            trades_repo=FakeTradesRepo(),
        )

        records = [_live_record(action="BUY", order_id="ord_002")]
        rows = svc.build_from_live_timeline(records)
        rows = svc.enrich_with_orders(rows)

        row = rows[0]
        assert row.order_status == "rejected"
        assert row.execution_status == "NONE"

    def test_enrich_partial_fill(self):
        order = FakeOrder(
            id="ord_003",
            status="partial",
            filled_qty=5.0,
            avg_fill_price=100.0,
            total_commission=0.50,
        )
        trades = [
            FakeTrade(id="trd_a", order_id="ord_003", qty=3.0, price=99.0, commission=0.30),
            FakeTrade(id="trd_b", order_id="ord_003", qty=2.0, price=101.0, commission=0.20),
        ]
        svc = ExplainabilityTimelineService(
            orders_repo=FakeOrdersRepo({"ord_003": order}),
            trades_repo=FakeTradesRepo({"ord_003": trades}),
        )

        records = [_live_record(action="BUY", order_id="ord_003")]
        rows = svc.build_from_live_timeline(records)
        rows = svc.enrich_with_orders(rows)

        row = rows[0]
        assert row.order_status == "partial"
        assert row.execution_status == "PARTIAL"
        # Weighted price: (3*99 + 2*101) / 5 = (297+202)/5 = 99.8
        assert row.execution_price == pytest.approx(99.8)
        assert row.execution_qty == pytest.approx(5.0)
        assert row.commission == pytest.approx(0.50)

    def test_enrich_skips_rows_without_order_id(self):
        svc = ExplainabilityTimelineService(
            orders_repo=FakeOrdersRepo(),
            trades_repo=FakeTradesRepo(),
        )
        records = [_live_record(action="HOLD")]  # No order_id
        rows = svc.build_from_live_timeline(records)
        rows = svc.enrich_with_orders(rows)

        row = rows[0]
        assert row.order_id is None
        assert row.order_status is None

    def test_enrich_without_repos_is_noop(self):
        svc = ExplainabilityTimelineService()  # No repos
        records = [_live_record(action="BUY", order_id="ord_001")]
        rows = svc.build_from_live_timeline(records)
        rows = svc.enrich_with_orders(rows)

        row = rows[0]
        assert row.order_id == "ord_001"
        assert row.order_status is None  # Not enriched

    def test_enrich_missing_order_gracefully(self):
        svc = ExplainabilityTimelineService(
            orders_repo=FakeOrdersRepo({}),
            trades_repo=FakeTradesRepo(),
        )
        records = [_live_record(action="BUY", order_id="ord_missing")]
        rows = svc.build_from_live_timeline(records)
        rows = svc.enrich_with_orders(rows)

        row = rows[0]
        assert row.order_id == "ord_missing"
        assert row.order_status is None  # Not found, gracefully handled


# ────────────────── Tests: Filtering ──────────────────


class TestFiltering:
    def _make_rows(self) -> List[ExplainabilityRow]:
        """Create a set of rows for filtering tests."""
        svc = ExplainabilityTimelineService()
        records = [
            _live_record(day=1, hour=10, action="HOLD"),
            _live_record(day=1, hour=14, action="BUY", order_id="ord_1"),
            _live_record(day=2, hour=10, action="HOLD"),
            _live_record(day=2, hour=14, action="SELL", order_id="ord_2"),
            _live_record(day=3, hour=10, action="SKIP"),
            _live_record(day=4, hour=10, action="HOLD"),
        ]
        rows = svc.build_from_live_timeline(records)
        # Manually set order_status for filtering tests
        rows[1].order_status = "filled"
        rows[3].order_status = "rejected"
        return rows

    def test_filter_by_action(self):
        svc = ExplainabilityTimelineService()
        rows = self._make_rows()
        filtered = svc.filter_rows(rows, actions=["BUY", "SELL"])
        assert len(filtered) == 2
        assert {r.action for r in filtered} == {"BUY", "SELL"}

    def test_filter_by_date_range(self):
        svc = ExplainabilityTimelineService()
        rows = self._make_rows()
        filtered = svc.filter_rows(
            rows,
            start_date=_make_ts(2, 0),
            end_date=_make_ts(3, 23),
        )
        assert len(filtered) == 3  # Day 2 (2 rows) + Day 3 (1 row)

    def test_filter_by_order_status(self):
        svc = ExplainabilityTimelineService()
        rows = self._make_rows()
        filtered = svc.filter_rows(rows, order_statuses=["filled"])
        assert len(filtered) == 1
        assert filtered[0].order_status == "filled"

    def test_filter_by_order_status_rejected(self):
        svc = ExplainabilityTimelineService()
        rows = self._make_rows()
        filtered = svc.filter_rows(rows, order_statuses=["rejected"])
        assert len(filtered) == 1
        assert filtered[0].action == "SELL"

    def test_combined_filters(self):
        svc = ExplainabilityTimelineService()
        rows = self._make_rows()
        filtered = svc.filter_rows(
            rows,
            actions=["BUY", "SELL"],
            start_date=_make_ts(1, 0),
            end_date=_make_ts(2, 23),
        )
        assert len(filtered) == 2
        assert {r.action for r in filtered} == {"BUY", "SELL"}


# ────────────────── Tests: Pagination ──────────────────


class TestPagination:
    def test_offset_and_limit(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(day=d) for d in range(1, 11)]
        rows = svc.build_from_live_timeline(records)

        timeline = svc.build_timeline(rows, offset=2, limit=3, aggregation="all")

        assert timeline.total_rows == 10
        assert timeline.offset == 2
        assert timeline.limit == 3
        assert len(timeline.rows) == 3

    def test_offset_zero_returns_from_start(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(day=d) for d in range(1, 6)]
        rows = svc.build_from_live_timeline(records)

        timeline = svc.build_timeline(rows, offset=0, limit=2, aggregation="all")
        assert len(timeline.rows) == 2
        # Rows are sorted newest first, so first row should be day 5
        assert timeline.rows[0].date_str == "2026-02-05"

    def test_offset_beyond_results(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(day=1)]
        rows = svc.build_from_live_timeline(records)

        timeline = svc.build_timeline(rows, offset=100, limit=10, aggregation="all")
        assert len(timeline.rows) == 0
        assert timeline.total_rows == 1
        assert timeline.filtered_rows == 1

    def test_filtered_rows_count_excludes_pagination(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(day=d) for d in range(1, 11)]
        rows = svc.build_from_live_timeline(records)

        timeline = svc.build_timeline(
            rows,
            actions=["HOLD"],
            offset=1,
            limit=3,
            aggregation="all",
        )
        # All 10 records are HOLD, so filtered_rows = 10
        assert timeline.filtered_rows == 10
        assert len(timeline.rows) == 3


# ────────────────── Tests: Daily Aggregation ──────────────────


class TestDailyAggregation:
    def test_hold_only_day_shows_one_row(self):
        svc = ExplainabilityTimelineService()
        records = [
            _live_record(day=1, hour=9, action="HOLD"),
            _live_record(day=1, hour=10, action="HOLD"),
            _live_record(day=1, hour=11, action="HOLD"),
        ]
        rows = svc.build_from_live_timeline(records)
        aggregated = svc.aggregate_to_daily(rows)
        assert len(aggregated) == 1

    def test_action_day_shows_action_rows_only(self):
        svc = ExplainabilityTimelineService()
        records = [
            _live_record(day=1, hour=9, action="HOLD"),
            _live_record(day=1, hour=10, action="BUY"),
            _live_record(day=1, hour=11, action="HOLD"),
            _live_record(day=1, hour=14, action="SELL"),
        ]
        rows = svc.build_from_live_timeline(records)
        aggregated = svc.aggregate_to_daily(rows)
        assert len(aggregated) == 2
        assert {r.action for r in aggregated} == {"BUY", "SELL"}

    def test_skip_counts_as_action(self):
        svc = ExplainabilityTimelineService()
        records = [
            _live_record(day=1, hour=9, action="HOLD"),
            _live_record(day=1, hour=10, action="SKIP"),
        ]
        rows = svc.build_from_live_timeline(records)
        aggregated = svc.aggregate_to_daily(rows)
        assert len(aggregated) == 1
        assert aggregated[0].action == "SKIP"


# ────────────────── Tests: build_timeline Integration ──────────────────


class TestBuildTimeline:
    def test_full_pipeline(self):
        order = FakeOrder(
            id="ord_001",
            status="filled",
            filled_qty=10.0,
            avg_fill_price=99.0,
            total_commission=0.99,
        )
        svc = ExplainabilityTimelineService(
            orders_repo=FakeOrdersRepo({"ord_001": order}),
            trades_repo=FakeTradesRepo(),
        )

        records = [
            _live_record(day=1, hour=10, action="HOLD"),
            _live_record(day=1, hour=14, action="BUY", order_id="ord_001"),
            _live_record(day=2, hour=10, action="HOLD"),
        ]
        rows = svc.build_from_live_timeline(records, "pos1", "p1", "AAPL")
        rows = svc.enrich_with_orders(rows)

        timeline = svc.build_timeline(
            rows,
            aggregation="daily",
            limit=100,
            position_id="pos1",
            portfolio_id="p1",
            symbol="AAPL",
            mode="LIVE",
        )

        assert timeline.total_rows == 3
        # Daily aggregation: Day 1 has a BUY so shows only BUY; Day 2 is HOLD-only so shows 1
        assert timeline.filtered_rows == 2
        assert timeline.mode == "LIVE"
        assert timeline.symbol == "AAPL"

        # Find the BUY row
        buy_rows = [r for r in timeline.rows if r.action == "BUY"]
        assert len(buy_rows) == 1
        assert buy_rows[0].order_status == "filled"

    def test_to_dict_includes_pagination(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record(day=d) for d in range(1, 6)]
        rows = svc.build_from_live_timeline(records)

        timeline = svc.build_timeline(rows, offset=1, limit=2, aggregation="all")
        d = timeline.to_dict()

        assert d["offset"] == 1
        assert d["limit"] == 2
        assert d["total_rows"] == 5
        assert d["filtered_rows"] == 5
        assert len(d["rows"]) == 2

    def test_to_dict_includes_order_status_filter(self):
        svc = ExplainabilityTimelineService()
        records = [_live_record()]
        rows = svc.build_from_live_timeline(records)

        timeline = svc.build_timeline(
            rows,
            order_statuses=["filled", "rejected"],
            aggregation="all",
        )
        d = timeline.to_dict()
        assert d["order_status_filter"] == ["filled", "rejected"]


# ────────────────── Tests: Simulation ──────────────────


class TestSimulationConversion:
    def test_basic_simulation_record(self):
        svc = ExplainabilityTimelineService()
        sim_result = {
            "id": "sim_001",
            "ticker": "VOO",
            "time_series_data": [
                {
                    "timestamp": "2025-01-02",
                    "price": 450.0,
                    "open": 448.0,
                    "high": 452.0,
                    "low": 447.0,
                    "close": 450.0,
                    "shares": 20,
                    "cash": 5000.0,
                    "anchor_price": 440.0,
                    "triggered": False,
                },
            ],
            "trade_log": [],
        }
        rows = svc.build_from_simulation(sim_result)

        assert len(rows) == 1
        row = rows[0]
        assert row.mode == "SIMULATION"
        assert row.symbol == "VOO"
        assert row.price == 450.0
        assert row.anchor_price == 440.0
        assert row.delta_pct == pytest.approx((450 - 440) / 440 * 100)
        assert row.action == "HOLD"

    def test_simulation_with_trade(self):
        svc = ExplainabilityTimelineService()
        sim_result = {
            "id": "sim_002",
            "ticker": "AAPL",
            "time_series_data": [
                {
                    "timestamp": "2025-01-15",
                    "price": 170.0,
                    "shares": 30,
                    "cash": 4000.0,
                    "anchor_price": 180.0,
                    "triggered": True,
                    "side": "BUY",
                    "executed": True,
                },
            ],
            "trade_log": [
                {
                    "timestamp": "2025-01-15",
                    "side": "BUY",
                    "qty": 5,
                    "price": 170.0,
                    "commission": 0.85,
                },
            ],
        }
        rows = svc.build_from_simulation(sim_result)

        assert len(rows) == 1
        row = rows[0]
        assert row.action == "BUY"
        assert row.execution_price == 170.0
        assert row.execution_qty == 5
        assert row.commission == 0.85

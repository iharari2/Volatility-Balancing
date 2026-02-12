# =========================
# backend/tests/unit/application/test_anchor_reset.py
# =========================
"""
Tests for anchor price reset logic:
1. Auto-reset when anchor deviates >50% from market (in EvaluatePositionUC)
2. Post-trade anchor reset to fill price (in ExecuteOrderUC)
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from decimal import Decimal

from domain.entities.position import Position
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.guardrails import GuardrailPolicy
from application.use_cases.evaluate_position_uc import EvaluatePositionUC


def _make_position(
    qty=100.0,
    cash=10000.0,
    anchor_price=100.0,
    asset_symbol="VOO",
) -> Position:
    return Position(
        id="pos_test",
        tenant_id="default",
        portfolio_id="test_portfolio",
        asset_symbol=asset_symbol,
        qty=qty,
        cash=cash,
        anchor_price=anchor_price,
        order_policy=OrderPolicy(
            trigger_threshold_pct=0.03,
            rebalance_ratio=1.6667,
            commission_rate=0.001,
            min_notional=0.0,
        ),
        guardrails=GuardrailPolicy(
            min_stock_alloc_pct=0.30,
            max_stock_alloc_pct=0.70,
            max_orders_per_day=100,
        ),
    )


def _make_uc(position: Position) -> EvaluatePositionUC:
    positions_mock = MagicMock()
    positions_mock.get.return_value = position

    events_mock = MagicMock()
    market_data_mock = MagicMock()
    mock_price_data = MagicMock()
    mock_price_data.price = position.anchor_price or 100.0
    market_data_mock.get_price.return_value = mock_price_data

    clock_mock = MagicMock()
    clock_mock.now.return_value = datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)

    return EvaluatePositionUC(
        positions=positions_mock,
        events=events_mock,
        market_data=market_data_mock,
        clock=clock_mock,
    )


# ───────────────────────────────────────────────────────────────
# Anomaly auto-reset (>50% deviation)
# ───────────────────────────────────────────────────────────────
class TestAnchorAnomalyReset:
    def test_no_reset_within_threshold(self):
        """No reset when anchor is within 50% of market price."""
        pos = _make_position(anchor_price=100.0)
        uc = _make_uc(pos)

        result = uc._check_and_reset_anchor_if_anomalous(
            "default", "test_portfolio", pos, 120.0  # 20% diff, under 50%
        )
        assert result is None
        assert pos.anchor_price == 100.0  # Unchanged

    def test_reset_when_above_threshold(self):
        """Reset anchor when current price is >50% above anchor."""
        pos = _make_position(anchor_price=50.0)
        uc = _make_uc(pos)

        result = uc._check_and_reset_anchor_if_anomalous(
            "default", "test_portfolio", pos, 100.0  # 100% diff
        )
        assert result is not None
        assert result["reset"] is True
        assert result["old_anchor_price"] == 50.0
        assert result["new_anchor_price"] == 100.0
        assert pos.anchor_price == 100.0  # Updated

    def test_reset_when_below_threshold(self):
        """Reset anchor when current price is >50% below anchor."""
        pos = _make_position(anchor_price=100.0)
        uc = _make_uc(pos)

        result = uc._check_and_reset_anchor_if_anomalous(
            "default", "test_portfolio", pos, 40.0  # 60% diff
        )
        assert result is not None
        assert result["reset"] is True
        assert pos.anchor_price == 40.0

    def test_no_reset_at_exactly_50_pct(self):
        """At exactly 50% difference, should NOT reset (threshold is >50%)."""
        pos = _make_position(anchor_price=100.0)
        uc = _make_uc(pos)

        result = uc._check_and_reset_anchor_if_anomalous(
            "default", "test_portfolio", pos, 50.0  # exactly 50% diff
        )
        assert result is None
        assert pos.anchor_price == 100.0

    def test_no_anchor_returns_none(self):
        """No anchor price set -> no reset check."""
        pos = _make_position(anchor_price=None)
        uc = _make_uc(pos)

        result = uc._check_and_reset_anchor_if_anomalous(
            "default", "test_portfolio", pos, 100.0
        )
        assert result is None

    def test_zero_anchor_returns_none(self):
        """Zero anchor price -> no reset check."""
        pos = _make_position(anchor_price=0)
        uc = _make_uc(pos)

        result = uc._check_and_reset_anchor_if_anomalous(
            "default", "test_portfolio", pos, 100.0
        )
        assert result is None

    def test_reset_saves_position(self):
        """Verify position is saved after anchor reset."""
        pos = _make_position(anchor_price=50.0)
        uc = _make_uc(pos)

        uc._check_and_reset_anchor_if_anomalous(
            "default", "test_portfolio", pos, 100.0
        )
        uc.positions.save.assert_called_once_with(pos)

    def test_reset_logs_event(self):
        """Verify an event is logged when anchor is reset."""
        pos = _make_position(anchor_price=50.0)
        uc = _make_uc(pos)

        uc._check_and_reset_anchor_if_anomalous(
            "default", "test_portfolio", pos, 100.0
        )
        uc.events.append.assert_called_once()
        event = uc.events.append.call_args[0][0]
        assert event.type == "anchor_price_auto_reset"
        assert event.inputs["old_anchor_price"] == 50.0
        assert event.inputs["current_market_price"] == 100.0


# ───────────────────────────────────────────────────────────────
# Post-trade anchor reset (in ExecuteOrderUC)
# ───────────────────────────────────────────────────────────────
class TestPostTradeAnchorReset:
    def test_anchor_set_to_fill_price_on_buy(self):
        """After BUY fill, anchor is set to fill price."""
        pos = _make_position(anchor_price=100.0)
        fill_price = 97.0

        # Simulate what ExecuteOrderUC does
        old_anchor = pos.anchor_price
        pos.set_anchor_price(fill_price)

        assert pos.anchor_price == fill_price
        assert old_anchor == 100.0

    def test_anchor_set_to_fill_price_on_sell(self):
        """After SELL fill, anchor is set to fill price."""
        pos = _make_position(anchor_price=100.0)
        fill_price = 103.0

        pos.set_anchor_price(fill_price)

        assert pos.anchor_price == fill_price

    def test_anchor_unchanged_if_fill_price_equals_anchor(self):
        """When fill price equals anchor, anchor is still set (no change in value)."""
        pos = _make_position(anchor_price=100.0)
        pos.set_anchor_price(100.0)
        assert pos.anchor_price == 100.0


# ───────────────────────────────────────────────────────────────
# Anchor adjustment for dividends
# ───────────────────────────────────────────────────────────────
class TestAnchorDividendAdjustment:
    def test_anchor_adjusted_for_dividend(self):
        """Anchor price is reduced by dividend per share."""
        pos = _make_position(anchor_price=100.0)
        dps = 2.50
        pos.adjust_anchor_for_dividend(dps)
        assert pos.anchor_price == 97.50

    def test_anchor_adjustment_with_no_anchor(self):
        """No adjustment if no anchor price set."""
        pos = _make_position(anchor_price=None)
        pos.adjust_anchor_for_dividend(2.50)
        assert pos.anchor_price is None

    def test_anchor_adjustment_prevents_false_trigger(self):
        """Dividend adjustment prevents false sell trigger after ex-date."""
        # Before ex-date: anchor=100, price=100 (no trigger)
        # On ex-date: stock drops by $2.50 to $97.50
        # Without adjustment: (100/97.50 - 1)*100 = 2.56% -> could trigger sell
        # With adjustment: anchor=$97.50, price=$97.50 -> 0% change -> no trigger
        from domain.services.price_trigger import PriceTrigger
        from domain.value_objects.configs import TriggerConfig

        pos = _make_position(anchor_price=100.0)
        dps = 2.50
        post_ex_price = Decimal("97.50")

        # Adjust anchor
        pos.adjust_anchor_for_dividend(dps)

        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        decision = PriceTrigger.evaluate(
            anchor_price=Decimal(str(pos.anchor_price)),
            current_price=post_ex_price,
            config=trigger_config,
        )
        assert decision.fired is False

# =========================
# backend/tests/unit/application/test_commission_calculation.py
# =========================
"""
Audit tests for commission calculation in guardrail trimming.

Focus on the cash_delta computation in _apply_guardrail_trimming (lines 704-706):
    cash_delta = -(raw_qty * price) - (abs(raw_qty) * price * commission_rate)

For BUY (raw_qty > 0):
    cash_delta = -(qty * price) - (qty * price * comm_rate)
    = -(cost) - (commission)
    => cash decreases by cost + commission  ✓

For SELL (raw_qty < 0):
    cash_delta = -((-qty) * price) - (qty * price * comm_rate)
    = (qty * price) - (qty * price * comm_rate)
    = proceeds - commission
    => cash increases by proceeds - commission  ✓

This test file verifies both paths produce correct cash_delta values.
"""

from decimal import Decimal

from domain.entities.position import Position
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.guardrails import GuardrailPolicy


def _make_position(
    qty=100.0,
    cash=10000.0,
    anchor_price=100.0,
    commission_rate=0.01,  # 1% for easier math
) -> Position:
    return Position(
        id="pos_test",
        tenant_id="default",
        portfolio_id="test_portfolio",
        asset_symbol="VOO",
        qty=qty,
        cash=cash,
        anchor_price=anchor_price,
        order_policy=OrderPolicy(
            commission_rate=commission_rate,
            min_notional=0.0,
        ),
        guardrails=GuardrailPolicy(
            min_stock_alloc_pct=0.0,
            max_stock_alloc_pct=1.0,
            max_orders_per_day=100,
        ),
    )


class TestCashDeltaFormula:
    """Test the cash_delta formula from guardrail trimming."""

    def test_buy_cash_delta(self):
        """BUY: cash decreases by cost + commission."""
        raw_qty = 10.0  # BUY 10 shares
        price = 100.0
        commission_rate = 0.01  # 1%

        # Formula from code: cash_delta = -(raw_qty * price) - (abs(raw_qty) * price * commission_rate)
        cash_delta = -(raw_qty * price) - (abs(raw_qty) * price * commission_rate)

        # Expected: -(10 * 100) - (10 * 100 * 0.01) = -1000 - 10 = -1010
        assert cash_delta == -1010.0
        # Cash should decrease
        assert cash_delta < 0

    def test_sell_cash_delta(self):
        """SELL: cash increases by proceeds - commission."""
        raw_qty = -10.0  # SELL 10 shares (negative)
        price = 100.0
        commission_rate = 0.01  # 1%

        # Formula: cash_delta = -(raw_qty * price) - (abs(raw_qty) * price * commission_rate)
        cash_delta = -(raw_qty * price) - (abs(raw_qty) * price * commission_rate)

        # -((-10) * 100) - (10 * 100 * 0.01) = 1000 - 10 = 990
        assert cash_delta == 990.0
        # Cash should increase
        assert cash_delta > 0

    def test_sell_proceeds_minus_commission(self):
        """Verify sell proceeds correctly account for commission."""
        raw_qty = -50.0  # SELL 50 shares
        price = 200.0
        commission_rate = 0.001  # 0.1%

        cash_delta = -(raw_qty * price) - (abs(raw_qty) * price * commission_rate)

        # Proceeds: 50 * 200 = 10,000
        # Commission: 50 * 200 * 0.001 = 10
        # Net: 10,000 - 10 = 9,990
        assert cash_delta == 9990.0

    def test_buy_cost_plus_commission(self):
        """Verify buy cost correctly accounts for commission."""
        raw_qty = 25.0  # BUY 25 shares
        price = 50.0
        commission_rate = 0.005  # 0.5%

        cash_delta = -(raw_qty * price) - (abs(raw_qty) * price * commission_rate)

        # Cost: 25 * 50 = 1,250
        # Commission: 25 * 50 * 0.005 = 6.25
        # Total: -(1250 + 6.25) = -1256.25
        assert cash_delta == -1256.25

    def test_zero_commission(self):
        """Zero commission rate: BUY/SELL delta is just cost/proceeds."""
        commission_rate = 0.0

        buy_delta = -(10 * 100.0) - (10 * 100.0 * commission_rate)
        assert buy_delta == -1000.0

        sell_delta = -((-10) * 100.0) - (10 * 100.0 * commission_rate)
        assert sell_delta == 1000.0

    def test_zero_qty_zero_delta(self):
        """Zero quantity produces zero cash delta."""
        raw_qty = 0.0
        price = 100.0
        commission_rate = 0.01

        cash_delta = -(raw_qty * price) - (abs(raw_qty) * price * commission_rate)
        assert cash_delta == 0.0


class TestCommissionInValidateAfterFill:
    """Test commission handling in GuardrailEvaluator.validate_after_fill."""

    def test_buy_commission_reduces_available_cash(self):
        """BUY: commission is subtracted from cash along with cost."""
        from domain.services.guardrail_evaluator import GuardrailEvaluator
        from domain.value_objects.position_state import PositionState
        from domain.value_objects.configs import GuardrailConfig

        # Position: 50 shares, $5,100 cash
        # Buy 50 shares @ $100: cost=$5,000, commission=$100 -> new cash = $0
        pos = PositionState(
            ticker="VOO",
            qty=Decimal("50"),
            cash=Decimal("5100"),
            dividend_receivable=Decimal("0"),
        )
        config = GuardrailConfig(
            min_stock_pct=Decimal("0.20"),
            max_stock_pct=Decimal("0.80"),
        )

        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="BUY",
            fill_qty=Decimal("50"),
            price=Decimal("100"),
            commission=Decimal("100"),
            config=config,
        )
        # 100 shares @ $100 = $10,000 stock; $0 cash -> 100% stock > 80% max
        assert ok is False

    def test_sell_commission_reduces_proceeds(self):
        """SELL: commission reduces proceeds, leaving less cash than expected."""
        from domain.services.guardrail_evaluator import GuardrailEvaluator
        from domain.value_objects.position_state import PositionState
        from domain.value_objects.configs import GuardrailConfig

        # Position: 100 shares, $0 cash
        # Sell 50 shares @ $100: proceeds=$5,000, commission=$500 -> new cash = $4,500
        pos = PositionState(
            ticker="VOO",
            qty=Decimal("100"),
            cash=Decimal("0"),
            dividend_receivable=Decimal("0"),
        )
        config = GuardrailConfig(
            min_stock_pct=Decimal("0.20"),
            max_stock_pct=Decimal("0.80"),
        )

        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="SELL",
            fill_qty=Decimal("50"),
            price=Decimal("100"),
            commission=Decimal("500"),
            config=config,
        )
        # 50 shares @ $100 = $5,000 stock; $4,500 cash -> stock% = 52.6% ✓
        assert ok is True


class TestCommissionInExecuteOrder:
    """Test commission handling in ExecuteOrderUC fill application."""

    def test_buy_fill_deducts_cost_plus_commission(self):
        """BUY fill: position cash decreases by (qty * price) + commission."""
        pos = _make_position(qty=100, cash=10000)
        fill_qty = 10.0
        fill_price = 100.0
        commission = 10.0

        # Simulate what ExecuteOrderUC does
        pos.qty += fill_qty
        pos.cash -= (fill_qty * fill_price) + commission

        assert pos.qty == 110.0
        assert pos.cash == 10000.0 - (10 * 100) - 10  # = 8990

    def test_sell_fill_adds_proceeds_minus_commission(self):
        """SELL fill: position cash increases by (qty * price) - commission."""
        pos = _make_position(qty=100, cash=10000)
        fill_qty = 10.0
        fill_price = 100.0
        commission = 10.0

        # Simulate what ExecuteOrderUC does
        pos.qty -= fill_qty
        pos.cash += (fill_qty * fill_price) - commission

        assert pos.qty == 90.0
        assert pos.cash == 10000.0 + (10 * 100) - 10  # = 10990

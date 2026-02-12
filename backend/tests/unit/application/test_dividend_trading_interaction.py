# =========================
# backend/tests/unit/application/test_dividend_trading_interaction.py
# =========================
"""
Tests for dividend + trading interaction.

Verifies:
1. Anchor adjustment on ex-dividend date prevents false triggers
2. Dividend receivable is included in effective cash for guardrail calculations
3. Dividend payment correctly transfers receivable to cash
4. End-to-end: ex-div → receivable → payment → trading continues correctly
"""

from decimal import Decimal

from domain.entities.position import Position
from domain.services.price_trigger import PriceTrigger
from domain.services.guardrail_evaluator import GuardrailEvaluator
from domain.value_objects.configs import TriggerConfig, GuardrailConfig
from domain.value_objects.decisions import TriggerDecision
from domain.value_objects.position_state import PositionState
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.guardrails import GuardrailPolicy


def _make_position(
    qty=100.0,
    cash=10000.0,
    anchor_price=100.0,
    dividend_receivable=0.0,
) -> Position:
    return Position(
        id="pos_test",
        tenant_id="default",
        portfolio_id="test_portfolio",
        asset_symbol="VOO",
        qty=qty,
        cash=cash,
        anchor_price=anchor_price,
        dividend_receivable=dividend_receivable,
        order_policy=OrderPolicy(
            trigger_threshold_pct=0.03,
            commission_rate=0.001,
        ),
        guardrails=GuardrailPolicy(
            min_stock_alloc_pct=0.30,
            max_stock_alloc_pct=0.70,
        ),
    )


def _make_position_state(
    qty="100",
    cash="10000",
    dividend_receivable="0",
    anchor_price=None,
) -> PositionState:
    return PositionState(
        ticker="VOO",
        qty=Decimal(qty),
        cash=Decimal(cash),
        dividend_receivable=Decimal(dividend_receivable),
        anchor_price=Decimal(anchor_price) if anchor_price else None,
    )


# ───────────────────────────────────────────────────────────────
# 1. Anchor adjustment prevents false triggers
# ───────────────────────────────────────────────────────────────
class TestAnchorDividendAdjustment:
    def test_without_adjustment_triggers_false_sell(self):
        """Without dividend adjustment, ex-date price drop triggers false sell."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        anchor = Decimal("100")
        # Stock drops by $4 DPS on ex-date
        post_ex_price = Decimal("96")  # -4% from anchor without adjustment

        decision = PriceTrigger.evaluate(anchor, post_ex_price, trigger_config)
        # Without adjustment, this would be a buy trigger (price dropped)
        assert decision.fired is True
        assert decision.direction == "buy"

    def test_with_adjustment_no_false_trigger(self):
        """With dividend adjustment, ex-date price drop does not trigger."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        dps = Decimal("4.0")
        anchor = Decimal("100") - dps  # Adjusted to $96
        post_ex_price = Decimal("96")

        decision = PriceTrigger.evaluate(anchor, post_ex_price, trigger_config)
        assert decision.fired is False

    def test_real_price_movement_still_triggers(self):
        """After dividend adjustment, genuine price movement still triggers."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        dps = Decimal("2.0")
        anchor = Decimal("100") - dps  # Adjusted to $98

        # Stock drops further to $94 (not just dividend)
        # Change from adjusted anchor: (94 - 98) / 98 * 100 = -4.08%
        post_ex_price = Decimal("94")
        decision = PriceTrigger.evaluate(anchor, post_ex_price, trigger_config)
        assert decision.fired is True
        assert decision.direction == "buy"


# ───────────────────────────────────────────────────────────────
# 2. Dividend receivable in effective cash for guardrails
# ───────────────────────────────────────────────────────────────
class TestDividendReceivableInGuardrails:
    def test_receivable_included_in_total_equity(self):
        """Dividend receivable increases total equity, affecting allocation calc."""
        # Without receivable: 100 @ $100 = $10,000 stock; $10,000 cash -> 50%
        # With $2,000 receivable: total = $22,000 -> stock% = 45.5%
        pos_without = _make_position_state(qty="100", cash="10000", dividend_receivable="0")
        pos_with = _make_position_state(qty="100", cash="10000", dividend_receivable="2000")

        config = GuardrailConfig(
            min_stock_pct=Decimal("0.30"),
            max_stock_pct=Decimal("0.70"),
        )
        trigger = TriggerDecision(fired=True, direction="buy", reason="Price dropped")
        price = Decimal("100")

        result_without = GuardrailEvaluator.evaluate(pos_without, trigger, config, price)
        result_with = GuardrailEvaluator.evaluate(pos_with, trigger, config, price)

        # Both should be allowed to buy
        assert result_without.allowed is True
        assert result_with.allowed is True
        # With receivable, more room to buy (lower current stock%)
        assert result_with.trade_intent.qty > result_without.trade_intent.qty

    def test_receivable_in_validate_after_fill(self):
        """validate_after_fill includes dividend receivable in effective cash."""
        # 50 @ $100 = $5,000 stock; $3,000 cash; $2,000 div recv
        # Effective cash = $5,000. Total = $10,000. Stock = 50%
        pos = _make_position_state(qty="50", cash="3000", dividend_receivable="2000")
        config = GuardrailConfig(
            min_stock_pct=Decimal("0.30"),
            max_stock_pct=Decimal("0.70"),
        )

        # Buy 10 shares: stock = $6,000, cash = $2,000, div recv = $2,000
        # total = $10,000, stock% = 60%
        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="BUY",
            fill_qty=Decimal("10"),
            price=Decimal("100"),
            commission=Decimal("0"),
            config=config,
        )
        assert ok is True

    def test_guardrail_sell_with_receivable(self):
        """SELL guardrail check with dividend receivable."""
        # 70 @ $100 = $7,000 stock; $2,000 cash; $1,000 div recv
        # Total = $10,000. Stock% = 70% -> at max
        pos = _make_position_state(qty="70", cash="2000", dividend_receivable="1000")
        config = GuardrailConfig(
            min_stock_pct=Decimal("0.30"),
            max_stock_pct=Decimal("0.70"),
        )

        # Sell trigger should be rejected since we're exactly at max (for sell, check min)
        trigger = TriggerDecision(fired=True, direction="sell", reason="Price rose")
        price = Decimal("100")
        result = GuardrailEvaluator.evaluate(pos, trigger, config, price)

        # At 70% stock, selling would bring us below max_stock_pct target of 30%
        # The sell targets min_stock_pct (0.30), and current is 0.70, so sell is allowed
        assert result.allowed is True


# ───────────────────────────────────────────────────────────────
# 3. Dividend payment transfers receivable to cash
# ───────────────────────────────────────────────────────────────
class TestDividendPayment:
    def test_clear_dividend_receivable_adds_to_cash(self):
        """clear_dividend_receivable moves receivable to cash."""
        pos = _make_position(qty=100, cash=10000, dividend_receivable=500.0)

        assert pos.cash == 10000.0
        assert pos.dividend_receivable == 500.0
        assert pos.get_effective_cash() == 10500.0

        # Process payment
        pos.clear_dividend_receivable(500.0)

        assert pos.cash == 10500.0
        assert pos.dividend_receivable == 0.0
        assert pos.get_effective_cash() == 10500.0

    def test_partial_receivable_clear(self):
        """Partial clearing of dividend receivable."""
        pos = _make_position(qty=100, cash=10000, dividend_receivable=1000.0)

        pos.clear_dividend_receivable(600.0)

        assert pos.cash == 10600.0
        assert pos.dividend_receivable == 400.0

    def test_effective_cash_before_payment(self):
        """Before payment, effective cash = cash + receivable."""
        pos = _make_position(qty=100, cash=10000, dividend_receivable=500.0)
        assert pos.get_effective_cash() == 10500.0

    def test_effective_cash_after_payment(self):
        """After payment, effective cash = cash (receivable is zero)."""
        pos = _make_position(qty=100, cash=10000, dividend_receivable=500.0)
        pos.clear_dividend_receivable(500.0)
        assert pos.get_effective_cash() == 10500.0
        assert pos.dividend_receivable == 0.0


# ───────────────────────────────────────────────────────────────
# 4. End-to-end: ex-div → receivable → payment → trading
# ───────────────────────────────────────────────────────────────
class TestDividendTradingEndToEnd:
    def test_full_dividend_cycle_no_false_triggers(self):
        """Complete dividend cycle: announcement → ex-date → payment → trading."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        guardrail_config = GuardrailConfig(
            min_stock_pct=Decimal("0.30"),
            max_stock_pct=Decimal("0.70"),
        )

        # Day 0: Position with anchor $100
        pos = _make_position(qty=100, cash=10000, anchor_price=100.0)

        # Day 1: Ex-dividend. DPS = $2.50, tax rate = 25%
        dps = 2.50
        net_dps = dps * (1 - 0.25)  # $1.875

        # Adjust anchor for dividend
        pos.adjust_anchor_for_dividend(dps)
        assert pos.anchor_price == 97.50

        # Add receivable (net amount)
        net_total = net_dps * pos.qty  # $187.50
        pos.add_dividend_receivable(net_total)
        assert pos.dividend_receivable == net_total

        # Stock price drops by DPS on ex-date
        ex_date_price = Decimal("97.50")

        # Verify no false trigger
        decision = PriceTrigger.evaluate(
            Decimal(str(pos.anchor_price)), ex_date_price, trigger_config
        )
        assert decision.fired is False

        # Day 2: Payment date. Receivable moves to cash.
        pos.clear_dividend_receivable(net_total)
        assert pos.dividend_receivable == 0.0
        assert pos.cash == 10000.0 + net_total  # $10,187.50

        # Day 3: Market moves. Price recovers to $100 (3% up from adjusted anchor $97.50)
        # Change from adjusted anchor: (100 - 97.50) / 97.50 * 100 = 2.56%
        # Still within band (< 3%), so no trigger
        decision = PriceTrigger.evaluate(
            Decimal(str(pos.anchor_price)), Decimal("100"), trigger_config
        )
        assert decision.fired is False

        # Price goes up more to $100.50 (3.08% from $97.50) -> sell trigger
        decision = PriceTrigger.evaluate(
            Decimal(str(pos.anchor_price)), Decimal("100.50"), trigger_config
        )
        assert decision.fired is True
        assert decision.direction == "sell"

        # Verify guardrail allows the sell
        pos_state = PositionState(
            ticker="VOO",
            qty=Decimal("100"),
            cash=Decimal(str(pos.cash)),
            dividend_receivable=Decimal("0"),
        )
        sell_result = GuardrailEvaluator.evaluate(
            pos_state, decision, guardrail_config, Decimal("100.50")
        )
        assert sell_result.allowed is True

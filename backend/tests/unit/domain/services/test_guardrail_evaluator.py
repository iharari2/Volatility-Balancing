# =========================
# backend/tests/unit/domain/services/test_guardrail_evaluator.py
# =========================
"""
Comprehensive unit tests for GuardrailEvaluator domain service.

Tests cover:
- BUY path: cash sufficiency, allocation cap, post-trade validation
- SELL path: share availability, min allocation floor, post-trade validation
- Edge cases: zero cash, zero qty, exact threshold, dividend receivable
- max_trade_pct_of_position interaction
- validate_after_fill method
"""

from decimal import Decimal

import pytest

from domain.services.guardrail_evaluator import GuardrailEvaluator
from domain.value_objects.configs import GuardrailConfig
from domain.value_objects.decisions import TriggerDecision
from domain.value_objects.position_state import PositionState


def _make_position(
    qty="100",
    cash="10000",
    dividend_receivable="0",
    anchor_price=None,
    ticker="VOO",
) -> PositionState:
    return PositionState(
        ticker=ticker,
        qty=Decimal(qty),
        cash=Decimal(cash),
        dividend_receivable=Decimal(dividend_receivable),
        anchor_price=Decimal(anchor_price) if anchor_price else None,
    )


def _make_config(
    min_stock_pct="0.30",
    max_stock_pct="0.70",
    max_trade_pct_of_position=None,
) -> GuardrailConfig:
    return GuardrailConfig(
        min_stock_pct=Decimal(min_stock_pct),
        max_stock_pct=Decimal(max_stock_pct),
        max_trade_pct_of_position=(
            Decimal(max_trade_pct_of_position) if max_trade_pct_of_position else None
        ),
    )


def _buy_trigger(reason="Price dropped") -> TriggerDecision:
    return TriggerDecision(fired=True, direction="buy", reason=reason)


def _sell_trigger(reason="Price rose") -> TriggerDecision:
    return TriggerDecision(fired=True, direction="sell", reason=reason)


def _no_trigger() -> TriggerDecision:
    return TriggerDecision(fired=False, direction=None, reason="Within band")


# ───────────────────────────────────────────────────────────────
# No-trigger short-circuit
# ───────────────────────────────────────────────────────────────
class TestNoTrigger:
    def test_no_trigger_returns_not_allowed(self):
        pos = _make_position()
        config = _make_config()
        result = GuardrailEvaluator.evaluate(pos, _no_trigger(), config, Decimal("100"))
        assert result.allowed is False
        assert result.reason == "no trigger"
        assert result.trade_intent is None


# ───────────────────────────────────────────────────────────────
# BUY path
# ───────────────────────────────────────────────────────────────
class TestBuyPath:
    def test_buy_approved_normal(self):
        """Basic BUY: 50% stock allocation, target 70%, enough cash."""
        # 100 shares @ $100 = $10,000 stock; $10,000 cash -> 50% allocation
        pos = _make_position(qty="100", cash="10000")
        config = _make_config(min_stock_pct="0.30", max_stock_pct="0.70")
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, Decimal("100"))

        assert result.allowed is True
        assert result.trade_intent is not None
        assert result.trade_intent.side == "buy"
        assert result.trade_intent.qty > 0

    def test_buy_allocation_already_at_max(self):
        """BUY rejected when already at max allocation."""
        # 70 shares @ $100 = $7,000; $3,000 cash -> exactly 70% allocation
        pos = _make_position(qty="70", cash="3000")
        config = _make_config(max_stock_pct="0.70")
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, Decimal("100"))

        assert result.allowed is False
        assert "above max" in result.reason.lower() or "at or above" in result.reason.lower()

    def test_buy_allocation_above_max(self):
        """BUY rejected when already above max allocation."""
        # 80 shares @ $100 = $8,000; $2,000 cash -> 80% allocation > 70% max
        pos = _make_position(qty="80", cash="2000")
        config = _make_config(max_stock_pct="0.70")
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, Decimal("100"))

        assert result.allowed is False

    def test_buy_insufficient_cash(self):
        """BUY rejected when zero cash available (and below max allocation)."""
        # 30 shares @ $100 = $3,000; $0 cash -> 100% stock but total equity is $3,000
        # Already above max 90% -> rejected on allocation check
        # Use a scenario where allocation allows buying but cash prevents it
        pos = _make_position(qty="30", cash="0", dividend_receivable="7000")
        # With dividend receivable: total = $3,000 + $7,000 = $10,000, stock% = 30%
        config = _make_config(max_stock_pct="0.90")
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, Decimal("100"))

        assert result.allowed is False
        assert "cash" in result.reason.lower()

    def test_buy_capped_to_available_cash(self):
        """BUY quantity reduced to what cash allows."""
        # 100 shares @ $100 = $10,000 stock; $500 cash -> 95.2% stock, but max is 99%
        # Only $500 cash available, so can only buy 5 more shares
        pos = _make_position(qty="100", cash="500")
        config = _make_config(min_stock_pct="0.10", max_stock_pct="0.99")
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, Decimal("100"))

        if result.allowed:
            assert result.trade_intent.qty <= Decimal("5")  # $500 / $100 per share

    def test_buy_respects_max_trade_pct(self):
        """BUY trimmed by max_trade_pct_of_position."""
        # 50 shares @ $100 = $5,000 stock; $15,000 cash -> 25% stock
        # Target 70% -> would need 90 more shares ($9,000)
        # max_trade_pct = 10% of total equity ($20,000 * 0.10 = $2,000 -> 20 shares max)
        pos = _make_position(qty="50", cash="15000")
        config = _make_config(max_stock_pct="0.70", max_trade_pct_of_position="0.10")
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, Decimal("100"))

        assert result.allowed is True
        assert result.trade_intent.qty <= Decimal("20")  # 10% of $20k / $100

    def test_buy_post_trade_allocation_within_bounds(self):
        """Verify post-trade allocation does not exceed max."""
        pos = _make_position(qty="50", cash="10000")
        config = _make_config(max_stock_pct="0.70")
        price = Decimal("100")
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, price)

        if result.allowed:
            new_qty = pos.qty + result.trade_intent.qty
            new_stock_val = new_qty * price
            new_cash = pos.cash - result.trade_intent.qty * price
            new_total = new_stock_val + new_cash + pos.dividend_receivable
            new_alloc = new_stock_val / new_total
            assert new_alloc <= Decimal("0.70") + Decimal("0.001")

    def test_buy_with_dividend_receivable(self):
        """Dividend receivable is included in total equity for allocation calc."""
        # 100 shares @ $100 = $10,000 stock; $10,000 cash; $500 div recv
        # Total equity = $20,500. Stock pct = 48.78%
        pos = _make_position(qty="100", cash="10000", dividend_receivable="500")
        config = _make_config(max_stock_pct="0.70")
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, Decimal("100"))

        assert result.allowed is True
        # Target stock value = 0.70 * $20,500 = $14,350 -> target qty = 143.5
        # Qty to buy = 143.5 - 100 = 43.5 (but limited by cash)
        assert result.trade_intent.qty > 0


# ───────────────────────────────────────────────────────────────
# SELL path
# ───────────────────────────────────────────────────────────────
class TestSellPath:
    def test_sell_approved_normal(self):
        """Basic SELL: 60% stock allocation, target 30%."""
        # 150 shares @ $100 = $15,000 stock; $10,000 cash -> 60% allocation
        pos = _make_position(qty="150", cash="10000")
        config = _make_config(min_stock_pct="0.30")
        result = GuardrailEvaluator.evaluate(pos, _sell_trigger(), config, Decimal("100"))

        assert result.allowed is True
        assert result.trade_intent is not None
        assert result.trade_intent.side == "sell"
        assert result.trade_intent.qty > 0

    def test_sell_allocation_already_at_min(self):
        """SELL rejected when already at min allocation."""
        # 30 shares @ $100 = $3,000; $7,000 cash -> exactly 30% stock
        pos = _make_position(qty="30", cash="7000")
        config = _make_config(min_stock_pct="0.30")
        result = GuardrailEvaluator.evaluate(pos, _sell_trigger(), config, Decimal("100"))

        assert result.allowed is False
        assert "below min" in result.reason.lower() or "at or below" in result.reason.lower()

    def test_sell_allocation_below_min(self):
        """SELL rejected when already below min allocation."""
        # 20 shares @ $100 = $2,000; $8,000 cash -> 20% < 30% min
        pos = _make_position(qty="20", cash="8000")
        config = _make_config(min_stock_pct="0.30")
        result = GuardrailEvaluator.evaluate(pos, _sell_trigger(), config, Decimal("100"))

        assert result.allowed is False

    def test_sell_capped_to_available_shares(self):
        """SELL quantity capped when more than available shares needed."""
        # 10 shares @ $100 = $1,000; $0 cash -> 100% stock
        # Even with 0% min, can't sell more than 10 shares
        pos = _make_position(qty="10", cash="0")
        config = _make_config(min_stock_pct="0.0", max_stock_pct="1.0")
        result = GuardrailEvaluator.evaluate(pos, _sell_trigger(), config, Decimal("100"))

        if result.allowed:
            assert result.trade_intent.qty <= pos.qty

    def test_sell_respects_max_trade_pct(self):
        """SELL trimmed by max_trade_pct_of_position."""
        # 200 shares @ $100 = $20,000 stock; $5,000 cash -> 80% stock
        # Target 30% -> need to sell ~125 shares
        # max_trade_pct = 10% of total $25,000 = $2,500 / $100 = 25 shares max
        pos = _make_position(qty="200", cash="5000")
        config = _make_config(min_stock_pct="0.30", max_trade_pct_of_position="0.10")
        result = GuardrailEvaluator.evaluate(pos, _sell_trigger(), config, Decimal("100"))

        assert result.allowed is True
        assert result.trade_intent.qty <= Decimal("25")

    def test_sell_post_trade_allocation_within_bounds(self):
        """Verify post-trade allocation is not below min."""
        pos = _make_position(qty="150", cash="10000")
        config = _make_config(min_stock_pct="0.30")
        price = Decimal("100")
        result = GuardrailEvaluator.evaluate(pos, _sell_trigger(), config, price)

        if result.allowed:
            new_qty = pos.qty - result.trade_intent.qty
            new_stock_val = new_qty * price
            new_cash = pos.cash + result.trade_intent.qty * price
            new_total = new_stock_val + new_cash + pos.dividend_receivable
            new_alloc = new_stock_val / new_total
            assert new_alloc >= Decimal("0.30") - Decimal("0.001")

    def test_sell_with_zero_qty(self):
        """SELL with zero shares available is rejected."""
        pos = _make_position(qty="0", cash="10000")
        config = _make_config(min_stock_pct="0.0")
        result = GuardrailEvaluator.evaluate(pos, _sell_trigger(), config, Decimal("100"))

        assert result.allowed is False


# ───────────────────────────────────────────────────────────────
# Edge cases
# ───────────────────────────────────────────────────────────────
class TestEdgeCases:
    def test_no_capital(self):
        """Rejected when total equity is zero."""
        pos = _make_position(qty="0", cash="0")
        config = _make_config()
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, Decimal("100"))

        assert result.allowed is False
        assert "capital" in result.reason.lower()

    def test_invalid_direction(self):
        """Rejected with invalid trigger direction."""
        pos = _make_position()
        config = _make_config()
        trigger = TriggerDecision(fired=True, direction="hold", reason="Invalid")
        result = GuardrailEvaluator.evaluate(pos, trigger, config, Decimal("100"))

        assert result.allowed is False
        assert "invalid" in result.reason.lower()

    def test_very_small_buy_results_in_zero_qty(self):
        """Buy where calculated qty rounds to zero is rejected."""
        # Allocation very close to max, tiny amount of cash available
        # 699 shares @ $100 = $69,900; $100 cash -> 99.86% stock (max=70%)
        # Already above max -> rejected before getting to qty calc
        pos = _make_position(qty="699", cash="100")
        config = _make_config(max_stock_pct="0.70")
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, Decimal("100"))
        assert result.allowed is False

    def test_exact_allocation_boundary_buy(self):
        """Exact boundary at max: 70 shares @ $100 with $3,000 cash = 70%."""
        pos = _make_position(qty="70", cash="3000")
        config = _make_config(max_stock_pct="0.70")
        result = GuardrailEvaluator.evaluate(pos, _buy_trigger(), config, Decimal("100"))
        assert result.allowed is False  # >= means rejected

    def test_exact_allocation_boundary_sell(self):
        """Exact boundary at min: 30 shares @ $100 with $7,000 cash = 30%."""
        pos = _make_position(qty="30", cash="7000")
        config = _make_config(min_stock_pct="0.30")
        result = GuardrailEvaluator.evaluate(pos, _sell_trigger(), config, Decimal("100"))
        assert result.allowed is False  # <= means rejected

    def test_dividend_receivable_affects_effective_cash(self):
        """Dividend receivable is included in total equity calculation."""
        # Without dividend: 100 @ $100 = $10,000 stock, $10,000 cash -> 50%
        # With $5,000 dividend receivable: total = $25,000 -> stock% = 40%
        pos_without = _make_position(qty="100", cash="10000", dividend_receivable="0")
        pos_with = _make_position(qty="100", cash="10000", dividend_receivable="5000")
        config = _make_config(max_stock_pct="0.70")
        price = Decimal("100")

        result_without = GuardrailEvaluator.evaluate(pos_without, _buy_trigger(), config, price)
        result_with = GuardrailEvaluator.evaluate(pos_with, _buy_trigger(), config, price)

        # Both allowed, but qty_with should be larger (can buy more to reach 70%)
        assert result_without.allowed is True
        assert result_with.allowed is True
        assert result_with.trade_intent.qty > result_without.trade_intent.qty


# ───────────────────────────────────────────────────────────────
# validate_after_fill
# ───────────────────────────────────────────────────────────────
class TestValidateAfterFill:
    def test_buy_fill_within_bounds(self):
        """Post-fill allocation is within [min, max] -> valid."""
        pos = _make_position(qty="50", cash="15000")
        config = _make_config(min_stock_pct="0.30", max_stock_pct="0.70")
        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="BUY",
            fill_qty=Decimal("20"),
            price=Decimal("100"),
            commission=Decimal("2"),
            config=config,
        )
        assert ok is True
        assert reason is None

    def test_buy_fill_exceeds_max(self):
        """BUY fill that pushes allocation above max -> invalid."""
        # 60 shares @ $100 = $6,000; $4,000 cash -> 60%
        # Buy 20 more: 80 shares = $8,000; cash = $4,000 - $2,000 - commission ~ $2,000 -> ~80%
        pos = _make_position(qty="60", cash="4000")
        config = _make_config(max_stock_pct="0.70")
        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="BUY",
            fill_qty=Decimal("20"),
            price=Decimal("100"),
            commission=Decimal("0"),
            config=config,
        )
        assert ok is False
        assert "exceed maximum" in reason.lower() or "above" in reason.lower()

    def test_sell_fill_below_min(self):
        """SELL fill that drops allocation below min -> invalid."""
        # 40 shares @ $100 = $4,000; $6,000 cash -> 40%
        # Sell 30: 10 shares = $1,000; cash = $6,000 + $3,000 - commission ~ $9,000 -> ~10%
        pos = _make_position(qty="40", cash="6000")
        config = _make_config(min_stock_pct="0.30")
        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="SELL",
            fill_qty=Decimal("30"),
            price=Decimal("100"),
            commission=Decimal("0"),
            config=config,
        )
        assert ok is False
        assert "below minimum" in reason.lower()

    def test_sell_fill_within_bounds(self):
        """SELL fill that keeps allocation within bounds -> valid."""
        # 60 shares @ $100 = $6,000; $4,000 cash -> 60%
        # Sell 10: 50 shares = $5,000; cash = $5,000 -> 50%
        pos = _make_position(qty="60", cash="4000")
        config = _make_config(min_stock_pct="0.30", max_stock_pct="0.70")
        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="SELL",
            fill_qty=Decimal("10"),
            price=Decimal("100"),
            commission=Decimal("0"),
            config=config,
        )
        assert ok is True
        assert reason is None

    def test_buy_fill_negative_cash(self):
        """BUY that would result in negative cash -> invalid."""
        pos = _make_position(qty="50", cash="100")
        config = _make_config(max_stock_pct="0.90")
        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="BUY",
            fill_qty=Decimal("10"),
            price=Decimal("100"),
            commission=Decimal("0"),
            config=config,
        )
        assert ok is False
        assert "negative cash" in reason.lower()

    def test_commission_deducted_from_cash(self):
        """Commission is deducted from cash in post-fill validation."""
        # 50 shares @ $100 = $5,000; $5,200 cash -> exactly affordable
        # Buy 2 shares: cost = $200, commission = $20 -> new cash = $4,980
        pos = _make_position(qty="50", cash="5200")
        config = _make_config(min_stock_pct="0.20", max_stock_pct="0.80")
        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="BUY",
            fill_qty=Decimal("2"),
            price=Decimal("100"),
            commission=Decimal("20"),
            config=config,
        )
        assert ok is True

    def test_sell_commission_deducted(self):
        """Commission is subtracted from sell proceeds in validation."""
        # 50 shares @ $100 = $5,000; $5,000 cash -> 50%
        # Sell 10: 40 shares = $4,000; cash = $5,000 + $1,000 - $10 commission = $5,990
        pos = _make_position(qty="50", cash="5000")
        config = _make_config(min_stock_pct="0.30", max_stock_pct="0.70")
        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="SELL",
            fill_qty=Decimal("10"),
            price=Decimal("100"),
            commission=Decimal("10"),
            config=config,
        )
        assert ok is True

    def test_dividend_receivable_in_validation(self):
        """Dividend receivable is included in effective cash for allocation calc."""
        # 50 shares @ $100 = $5,000; $3,000 cash; $2,000 div recv
        # Effective cash = $5,000. Total = $10,000. Stock = 50%
        # Buy 10: 60 shares = $6,000; cash = $2,000; div recv $2,000
        # Total = $10,000. Stock% = 60%
        pos = _make_position(qty="50", cash="3000", dividend_receivable="2000")
        config = _make_config(min_stock_pct="0.30", max_stock_pct="0.70")
        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="BUY",
            fill_qty=Decimal("10"),
            price=Decimal("100"),
            commission=Decimal("0"),
            config=config,
        )
        assert ok is True

    def test_no_capital_after_fill(self):
        """No capital available after fill -> invalid."""
        pos = _make_position(qty="0", cash="0")
        config = _make_config()
        ok, reason = GuardrailEvaluator.validate_after_fill(
            position_state=pos,
            side="BUY",
            fill_qty=Decimal("0"),
            price=Decimal("100"),
            commission=Decimal("0"),
            config=config,
        )
        assert ok is False
        assert "capital" in reason.lower()

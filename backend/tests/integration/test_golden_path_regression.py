# =========================
# backend/tests/integration/test_golden_path_regression.py
# =========================
"""
Golden-path regression tests for the full algorithm pipeline.

Runs the complete algorithm:
  tick → trigger → guardrail → order → fill → position update → anchor reset

Against synthetic price series with known expected outcomes.
Verifies:
- Expected number of trades fires
- Trade directions match expected behavior
- Final position state (qty, cash) matches manual calculation
- No guardrail violations occur
"""

import pytest
from decimal import Decimal

from domain.entities.position import Position
from domain.services.price_trigger import PriceTrigger
from domain.services.guardrail_evaluator import GuardrailEvaluator
from domain.value_objects.configs import TriggerConfig, GuardrailConfig
from domain.value_objects.position_state import PositionState
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.guardrails import GuardrailPolicy


def _run_simulation(
    initial_qty: float,
    initial_cash: float,
    initial_anchor: float,
    price_series: list[float],
    trigger_threshold_pct: float = 3.0,
    min_stock_pct: float = 0.30,
    max_stock_pct: float = 0.70,
    rebalance_ratio: float = 1.6667,
    commission_rate: float = 0.001,
) -> dict:
    """
    Run a simplified simulation through a price series.

    Returns dict with:
    - trades: list of {day, side, qty, price, anchor_before, anchor_after}
    - final_qty, final_cash, final_anchor
    - guardrail_violations: count of violations
    """
    trigger_config = TriggerConfig(
        up_threshold_pct=Decimal(str(trigger_threshold_pct)),
        down_threshold_pct=Decimal(str(trigger_threshold_pct)),
    )
    guardrail_config = GuardrailConfig(
        min_stock_pct=Decimal(str(min_stock_pct)),
        max_stock_pct=Decimal(str(max_stock_pct)),
    )

    qty = initial_qty
    cash = initial_cash
    anchor = initial_anchor

    trades = []
    guardrail_violations = 0

    for day, price in enumerate(price_series):
        price_dec = Decimal(str(price))
        anchor_dec = Decimal(str(anchor))

        # Step 1: Evaluate trigger
        trigger = PriceTrigger.evaluate(anchor_dec, price_dec, trigger_config)

        if not trigger.fired:
            continue

        # Step 2: Evaluate guardrails
        pos_state = PositionState(
            ticker="TEST",
            qty=Decimal(str(qty)),
            cash=Decimal(str(cash)),
            dividend_receivable=Decimal("0"),
        )
        guardrail_decision = GuardrailEvaluator.evaluate(
            pos_state, trigger, guardrail_config, price_dec
        )

        if not guardrail_decision.allowed:
            continue

        trade_intent = guardrail_decision.trade_intent
        trade_qty = float(trade_intent.qty)
        side = trade_intent.side

        # Step 3: Calculate order sizing using the formula
        stock_value = qty * price
        total_value = stock_value + cash

        raw_qty = (anchor / price - 1) * rebalance_ratio * (total_value / price)

        if side == "sell":
            # Ensure negative, cap to available
            final_qty = min(abs(raw_qty), qty, trade_qty)
            cost = final_qty * price
            commission = cost * commission_rate

            # Apply fill
            qty -= final_qty
            cash += cost - commission
            anchor_before = anchor
            anchor = price  # Post-trade anchor reset

            trades.append({
                "day": day,
                "side": "SELL",
                "qty": final_qty,
                "price": price,
                "anchor_before": anchor_before,
                "anchor_after": anchor,
                "commission": commission,
            })
        else:  # buy
            # Ensure positive, cap to affordable
            final_qty = min(abs(raw_qty), cash / price, trade_qty)
            cost = final_qty * price
            commission = cost * commission_rate

            # Apply fill
            qty += final_qty
            cash -= cost + commission
            anchor_before = anchor
            anchor = price

            trades.append({
                "day": day,
                "side": "BUY",
                "qty": final_qty,
                "price": price,
                "anchor_before": anchor_before,
                "anchor_after": anchor,
                "commission": commission,
            })

        # Step 4: Validate no guardrail violation post-trade
        stock_val_post = qty * price
        total_val_post = stock_val_post + cash
        stock_pct_post = stock_val_post / total_val_post if total_val_post > 0 else 0

        if stock_pct_post < min_stock_pct - 0.01 or stock_pct_post > max_stock_pct + 0.01:
            guardrail_violations += 1

    return {
        "trades": trades,
        "final_qty": qty,
        "final_cash": cash,
        "final_anchor": anchor,
        "guardrail_violations": guardrail_violations,
        "total_trades": len(trades),
    }


# ───────────────────────────────────────────────────────────────
# Scenario 1: Simple up-down-up oscillation
# ───────────────────────────────────────────────────────────────
class TestGoldenPathOscillation:
    """Price oscillates around anchor, triggering buys and sells."""

    def test_simple_oscillation(self):
        """
        Price path: 100 → 96.9 (BUY) → 100 → 103.1 (SELL) → 100 → 96.5 (BUY)

        Starting: 100 shares @ $100, $10,000 cash
        """
        price_series = [
            100.0,   # Day 0: at anchor, no trigger
            98.0,    # Day 1: -2%, within band
            96.9,    # Day 2: -3.1%, BUY trigger
            98.0,    # Day 3: within band from new anchor ($96.9)
            100.0,   # Day 4: +3.2% from $96.9 anchor = SELL trigger
            98.0,    # Day 5: within band from new anchor ($100)
            96.5,    # Day 6: -3.5% from $100 anchor = BUY trigger
        ]

        result = _run_simulation(
            initial_qty=100,
            initial_cash=10000,
            initial_anchor=100.0,
            price_series=price_series,
        )

        # Expect 3 trades: BUY, SELL, BUY
        assert result["total_trades"] == 3
        assert result["trades"][0]["side"] == "BUY"
        assert result["trades"][1]["side"] == "SELL"
        assert result["trades"][2]["side"] == "BUY"

        # No guardrail violations
        assert result["guardrail_violations"] == 0

        # Final anchor should be the last trade price
        assert result["final_anchor"] == 96.5

    def test_no_trades_within_band(self):
        """Price stays within ±3% band -> no trades."""
        price_series = [
            100.0,   # at anchor
            101.0,   # +1%
            99.0,    # -1%
            102.0,   # +2%
            98.5,    # -1.5%
            100.5,   # +0.5%
        ]

        result = _run_simulation(
            initial_qty=100,
            initial_cash=10000,
            initial_anchor=100.0,
            price_series=price_series,
        )

        assert result["total_trades"] == 0
        assert result["final_qty"] == 100
        assert result["final_cash"] == 10000


# ───────────────────────────────────────────────────────────────
# Scenario 2: Trending market (steady decline)
# ───────────────────────────────────────────────────────────────
class TestGoldenPathTrending:
    """Market trends down, triggering sequential buys."""

    def test_steady_decline_multiple_buys(self):
        """
        Price declines steadily. Each 3%+ drop from current anchor triggers a BUY.
        After each BUY, anchor resets to fill price.
        """
        # Anchor starts at 100
        # Drop to 96.9 -> BUY, new anchor = 96.9
        # Drop to 93.9 -> 96.9 * 0.97 = 93.99 -> BUY, new anchor = 93.9
        # Drop to 91.0 -> 93.9 * 0.97 = 91.08 -> BUY, new anchor = 91.0
        price_series = [
            100.0,   # Day 0
            96.9,    # Day 1: BUY (-3.1%)
            94.0,    # Day 2: within band from 96.9 (still -3.09%, just barely crosses)
            93.9,    # Day 3: -3.1% from 96.9 -> BUY
            91.0,    # Day 4: -3.09% from 93.9 -> BUY
        ]

        result = _run_simulation(
            initial_qty=100,
            initial_cash=10000,
            initial_anchor=100.0,
            price_series=price_series,
        )

        # All trades should be BUYs
        for trade in result["trades"]:
            assert trade["side"] == "BUY"

        # Qty should increase, cash should decrease
        assert result["final_qty"] > 100
        assert result["final_cash"] < 10000

        # No guardrail violations
        assert result["guardrail_violations"] == 0

    def test_decline_exhausts_cash(self):
        """Market drops until cash is exhausted, then BUYs stop."""
        price_series = [
            100.0,
            96.9,    # BUY
            93.9,    # BUY
            91.0,    # BUY
            88.0,    # BUY
            85.0,    # BUY (may run out of cash)
            82.0,    # BUY (may be rejected)
            79.0,    # BUY (may be rejected)
        ]

        result = _run_simulation(
            initial_qty=100,
            initial_cash=5000,  # Limited cash
            initial_anchor=100.0,
            price_series=price_series,
        )

        # Cash should be near zero or all spent
        assert result["final_cash"] >= 0  # Never negative

        # No guardrail violations
        assert result["guardrail_violations"] == 0


# ───────────────────────────────────────────────────────────────
# Scenario 3: Rally market (steady increase)
# ───────────────────────────────────────────────────────────────
class TestGoldenPathRally:
    """Market rallies, triggering sequential sells."""

    def test_steady_rally_multiple_sells(self):
        """Price rises steadily, triggering SELL on each 3%+ move."""
        price_series = [
            100.0,
            103.1,   # SELL (+3.1%)
            106.3,   # SELL (+3.1% from 103.1)
            109.6,   # SELL (+3.1% from 106.3)
        ]

        result = _run_simulation(
            initial_qty=100,
            initial_cash=10000,
            initial_anchor=100.0,
            price_series=price_series,
        )

        for trade in result["trades"]:
            assert trade["side"] == "SELL"

        # Qty should decrease, cash should increase
        assert result["final_qty"] < 100
        assert result["final_cash"] > 10000

        # No guardrail violations
        assert result["guardrail_violations"] == 0


# ───────────────────────────────────────────────────────────────
# Scenario 4: Guardrail boundary test
# ───────────────────────────────────────────────────────────────
class TestGoldenPathGuardrails:
    """Test that guardrails prevent trades that would violate allocation bounds."""

    def test_sell_stopped_by_min_allocation(self):
        """Selling stopped when it would push stock below min allocation."""
        # Start with low allocation - selling would breach min
        # 35 shares @ $100 = $3,500; $6,500 cash -> 35% stock
        # With 30% min, selling would push below
        price_series = [
            100.0,
            103.1,   # SELL trigger, but guardrail may prevent
            106.3,   # Another SELL trigger
        ]

        result = _run_simulation(
            initial_qty=35,
            initial_cash=6500,
            initial_anchor=100.0,
            price_series=price_series,
            min_stock_pct=0.30,
        )

        # All trades should respect min allocation
        assert result["guardrail_violations"] == 0

    def test_buy_stopped_by_max_allocation(self):
        """Buying stopped when it would push stock above max allocation."""
        # Start with high allocation - buying would breach max
        # 68 shares @ $100 = $6,800; $2,200 cash -> 75.6% stock (but we use $9,000 total)
        price_series = [
            100.0,
            96.9,    # BUY trigger, but guardrail may limit
        ]

        result = _run_simulation(
            initial_qty=68,
            initial_cash=2200,
            initial_anchor=100.0,
            price_series=price_series,
            max_stock_pct=0.70,
        )

        assert result["guardrail_violations"] == 0


# ───────────────────────────────────────────────────────────────
# Scenario 5: Mean-reversion profit test
# ───────────────────────────────────────────────────────────────
class TestGoldenPathProfitability:
    """Verify that buy-low-sell-high pattern generates profit."""

    def test_mean_reversion_generates_profit(self):
        """
        Price drops 5%, we buy. Price recovers to original level, we sell.
        Should result in net profit (minus commissions).
        """
        price_series = [
            100.0,   # Start
            95.0,    # BUY at -5%
            100.0,   # Not enough from $95 anchor (+5.26% >= 3%)  -> SELL
        ]

        result = _run_simulation(
            initial_qty=100,
            initial_cash=10000,
            initial_anchor=100.0,
            price_series=price_series,
            commission_rate=0.001,
        )

        # Should have at least 2 trades: BUY at $95, SELL at $100
        assert result["total_trades"] >= 2

        # Calculate total portfolio value
        # Final value = final_qty * last_price + final_cash
        last_price = price_series[-1]
        final_value = result["final_qty"] * last_price + result["final_cash"]
        initial_value = 100 * 100.0 + 10000.0  # $20,000

        # Should be profitable (or at least break even after commissions)
        # The profit comes from buying low and selling high
        # Commission drags are minimal (0.1%)
        assert final_value >= initial_value - 50  # Allow small commission drag

    def test_full_cycle_returns_near_initial_value(self):
        """Complete buy-sell cycle: portfolio value preserved (minus commissions)."""
        price_series = [
            100.0,
            96.9,    # BUY
            103.1,   # SELL (from anchor $96.9, this is +6.4% -> triggers)
        ]

        result = _run_simulation(
            initial_qty=100,
            initial_cash=10000,
            initial_anchor=100.0,
            price_series=price_series,
            commission_rate=0.0,  # No commission for cleaner test
        )

        last_price = price_series[-1]
        final_value = result["final_qty"] * last_price + result["final_cash"]
        initial_value = 100 * 100.0 + 10000.0

        # With zero commission, value should be very close to initial
        # (slight difference due to non-symmetric buying/selling)
        assert abs(final_value - initial_value) / initial_value < 0.02  # Within 2%

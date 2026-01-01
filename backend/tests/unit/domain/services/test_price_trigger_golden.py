# =========================
# backend/tests/unit/domain/services/test_price_trigger_golden.py
# =========================
"""
Golden Test Scenarios for PriceTrigger Domain Service

These tests implement Scenario A and Scenario B from backend/docs/testing_scenarios.md
at the domain service level (pure logic, no infrastructure).
"""

from decimal import Decimal

from domain.services.price_trigger import PriceTrigger
from domain.value_objects.configs import TriggerConfig


class TestScenarioA_PriceTrigger_NoTradeInsideBand:
    """
    Scenario A – No Trade Inside Trigger Band (Domain Level)

    Verify that PriceTrigger does not fire when price movements stay within the trigger band.
    """

    def test_scenario_a_all_prices_within_band(self):
        """Test that no triggers fire for prices within ±3% band."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        anchor_price = Decimal("100")

        # Price path - all within trigger band
        test_cases = [
            (Decimal("101"), "+1.0%"),  # +1.0% vs anchor
            (Decimal("102"), "+2.0%"),  # +2.0%
            (Decimal("101.5"), "+1.5%"),  # +1.5%
            (Decimal("99.9"), "-0.1%"),  # -0.1%
        ]

        for price, description in test_cases:
            decision = PriceTrigger.evaluate(
                anchor_price=anchor_price,
                current_price=price,
                config=trigger_config,
            )
            assert (
                decision.fired is False
            ), f"Price {price} ({description}) should not trigger (within ±3% band)"
            assert decision.direction is None
            assert "within" in decision.reason.lower() or "no" in decision.reason.lower()

    def test_scenario_a_exact_threshold_boundary(self):
        """Test that exact threshold values are handled correctly."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        anchor_price = Decimal("100")

        # Exactly at +3% threshold
        price_at_up = Decimal("103.0")
        decision_up = PriceTrigger.evaluate(anchor_price, price_at_up, trigger_config)
        assert decision_up.fired is True
        assert decision_up.direction == "sell"

        # Exactly at -3% threshold
        price_at_down = Decimal("97.0")
        decision_down = PriceTrigger.evaluate(anchor_price, price_at_down, trigger_config)
        assert decision_down.fired is True
        assert decision_down.direction == "buy"

        # Just inside +3% (e.g., 102.99)
        price_just_inside = Decimal("102.99")
        decision_inside = PriceTrigger.evaluate(anchor_price, price_just_inside, trigger_config)
        assert decision_inside.fired is False


class TestScenarioB_PriceTrigger_BuyAndSell:
    """
    Scenario B – Simple Buy and Sell Cycle (Domain Level)

    Validate that PriceTrigger fires correctly when thresholds are crossed.
    """

    def test_scenario_b_buy_trigger(self):
        """Test BUY trigger at t1 (96.9, -3.1%)."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        anchor_price = Decimal("100")
        price_t1 = Decimal("96.9")  # -3.1%

        decision = PriceTrigger.evaluate(anchor_price, price_t1, trigger_config)

        assert decision.fired is True
        assert decision.direction == "buy"
        assert "down" in decision.reason.lower() or "buy" in decision.reason.lower()

    def test_scenario_b_no_trigger_at_anchor(self):
        """Test no trigger at t2 (100, back near anchor)."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        anchor_price = Decimal("100")
        price_t2 = Decimal("100")

        decision = PriceTrigger.evaluate(anchor_price, price_t2, trigger_config)

        assert decision.fired is False
        assert decision.direction is None

    def test_scenario_b_sell_trigger(self):
        """Test SELL trigger at t3 (103.2, +3.2%)."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        anchor_price = Decimal("100")
        price_t3 = Decimal("103.2")  # +3.2%

        decision = PriceTrigger.evaluate(anchor_price, price_t3, trigger_config)

        assert decision.fired is True
        assert decision.direction == "sell"
        assert "up" in decision.reason.lower() or "sell" in decision.reason.lower()

    def test_scenario_b_no_anchor_price(self):
        """Test that no trigger fires when anchor price is None."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        anchor_price = None
        current_price = Decimal("96.9")

        decision = PriceTrigger.evaluate(anchor_price, current_price, trigger_config)

        assert decision.fired is False
        assert decision.direction is None
        assert "anchor" in decision.reason.lower()

    def test_scenario_b_zero_anchor_price(self):
        """Test that no trigger fires when anchor price is zero."""
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        anchor_price = Decimal("0")
        current_price = Decimal("96.9")

        decision = PriceTrigger.evaluate(anchor_price, current_price, trigger_config)

        assert decision.fired is False
        assert decision.direction is None

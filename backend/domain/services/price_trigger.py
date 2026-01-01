# =========================
# backend/domain/services/price_trigger.py
# =========================
from decimal import Decimal
from typing import Optional

from domain.value_objects.configs import TriggerConfig
from domain.value_objects.decisions import TriggerDecision


class PriceTrigger:
    """Pure domain service for evaluating price triggers."""

    @staticmethod
    def evaluate(
        anchor_price: Optional[Decimal],
        current_price: Decimal,
        config: TriggerConfig,
    ) -> TriggerDecision:
        """
        Pure function to evaluate price triggers.

        - If no anchor -> no trigger.
        - Compute percentage move from anchor.
        - If >= up_threshold_pct => fired, direction="sell"
        - If <= -down_threshold_pct => fired, direction="buy"
        - Else => fired=False
        """
        if anchor_price is None or anchor_price == 0:
            return TriggerDecision(fired=False, direction=None, reason="No anchor price set")

        # Calculate percentage move from anchor
        # Positive means price went up (sell signal)
        # Negative means price went down (buy signal)
        price_change_pct = ((current_price - anchor_price) / anchor_price) * Decimal("100")

        # Check sell trigger (price went up)
        if price_change_pct >= config.up_threshold_pct:
            return TriggerDecision(
                fired=True,
                direction="sell",
                reason=f"Price moved up {price_change_pct:.2f}% (threshold: {config.up_threshold_pct}%)",
            )

        # Check buy trigger (price went down)
        if price_change_pct <= -config.down_threshold_pct:
            return TriggerDecision(
                fired=True,
                direction="buy",
                reason=f"Price moved down {abs(price_change_pct):.2f}% (threshold: {config.down_threshold_pct}%)",
            )

        # No trigger
        return TriggerDecision(
            fired=False,
            direction=None,
            reason=f"Price change {price_change_pct:.2f}% within thresholds",
        )

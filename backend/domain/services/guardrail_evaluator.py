# =========================
# backend/domain/services/guardrail_evaluator.py
# =========================
from decimal import Decimal

from domain.value_objects.position_state import PositionState
from domain.value_objects.configs import GuardrailConfig
from domain.value_objects.decisions import GuardrailDecision, TriggerDecision
from domain.value_objects.trade_intent import TradeIntent


class GuardrailEvaluator:
    """Pure domain service for evaluating guardrails and generating trade intents."""

    @staticmethod
    def evaluate(
        position_state: PositionState,
        trigger_decision: TriggerDecision,
        config: GuardrailConfig,
        price: Decimal,
    ) -> GuardrailDecision:
        """
        Pure function to evaluate guardrails and generate trade intent.

        Responsibilities:
        - If trigger_decision.fired is False => allowed=False, reason="no trigger"
        - Compute current stock value and total equity (stock + cash + dividend receivable).
        - Compute current allocation.
        - For "buy": ensure result allocation <= max_stock_pct.
        - For "sell": ensure result allocation >= min_stock_pct.
        - Derive a TradeIntent with a qty that respects:
            - allocation bounds
            - max_trade_pct_of_position if provided
        - If impossible to trade without violating guardrail => allowed=False.
        """
        # No trigger, no trade
        if not trigger_decision.fired:
            return GuardrailDecision(allowed=False, reason="no trigger")

        # Calculate current state
        stock_value = position_state.qty * price
        effective_cash = position_state.cash + position_state.dividend_receivable
        total_equity = stock_value + effective_cash

        # Handle edge case: no capital
        if total_equity <= 0:
            return GuardrailDecision(allowed=False, reason="No capital available")

        # Current allocation
        current_stock_pct = stock_value / total_equity if total_equity > 0 else Decimal("0")

        direction = trigger_decision.direction
        if direction not in ("buy", "sell"):
            return GuardrailDecision(allowed=False, reason=f"Invalid direction: {direction}")

        # Calculate target allocation based on direction
        if direction == "buy":
            # Buy: target is max_stock_pct (we want to increase allocation)
            target_stock_pct = config.max_stock_pct
            if current_stock_pct >= target_stock_pct:
                return GuardrailDecision(
                    allowed=False,
                    reason=f"Already at or above max allocation {current_stock_pct:.2%} >= {target_stock_pct:.2%}",
                )

            # Calculate how much stock value we need to reach target
            target_stock_value = target_stock_pct * total_equity
            target_qty = target_stock_value / price
            qty_to_buy = target_qty - position_state.qty

            # Apply max_trade_pct_of_position limit if provided
            if config.max_trade_pct_of_position is not None:
                max_trade_notional = total_equity * config.max_trade_pct_of_position
                max_qty = max_trade_notional / price
                if qty_to_buy > max_qty:
                    qty_to_buy = max_qty

            # Check if we have enough cash
            cost = qty_to_buy * price
            if cost > position_state.cash:
                # Can't afford full amount, buy what we can
                qty_to_buy = position_state.cash / price
                if qty_to_buy <= 0:
                    return GuardrailDecision(allowed=False, reason="Insufficient cash for buy")

            # Verify post-trade allocation
            post_qty = position_state.qty + qty_to_buy
            post_stock_value = post_qty * price
            post_cash = position_state.cash - (qty_to_buy * price)
            post_total = post_stock_value + post_cash + position_state.dividend_receivable
            post_stock_pct = post_stock_value / post_total if post_total > 0 else Decimal("0")

            if post_stock_pct > config.max_stock_pct:
                return GuardrailDecision(
                    allowed=False,
                    reason=f"Post-trade allocation {post_stock_pct:.2%} would exceed max {config.max_stock_pct:.2%}",
                )

            if qty_to_buy <= 0:
                return GuardrailDecision(
                    allowed=False, reason="Calculated buy quantity is zero or negative"
                )

            return GuardrailDecision(
                allowed=True,
                reason=f"Buy approved: {qty_to_buy:.4f} shares to reach {target_stock_pct:.2%} allocation",
                trade_intent=TradeIntent(
                    side="buy", qty=qty_to_buy, reason=trigger_decision.reason
                ),
            )

        else:  # direction == "sell"
            # Sell: target is min_stock_pct (we want to decrease allocation)
            target_stock_pct = config.min_stock_pct
            if current_stock_pct <= target_stock_pct:
                return GuardrailDecision(
                    allowed=False,
                    reason=f"Already at or below min allocation {current_stock_pct:.2%} <= {target_stock_pct:.2%}",
                )

            # Calculate how much stock value we need to sell to reach target
            target_stock_value = target_stock_pct * total_equity
            target_qty = target_stock_value / price
            qty_to_sell = position_state.qty - target_qty

            # Can't sell more than we have
            if qty_to_sell > position_state.qty:
                qty_to_sell = position_state.qty

            # Apply max_trade_pct_of_position limit if provided
            if config.max_trade_pct_of_position is not None:
                max_trade_notional = total_equity * config.max_trade_pct_of_position
                max_qty = max_trade_notional / price
                if qty_to_sell > max_qty:
                    qty_to_sell = max_qty

            # Verify post-trade allocation
            post_qty = position_state.qty - qty_to_sell
            post_stock_value = post_qty * price
            post_cash = position_state.cash + (qty_to_sell * price)
            post_total = post_stock_value + post_cash + position_state.dividend_receivable
            post_stock_pct = post_stock_value / post_total if post_total > 0 else Decimal("0")

            if post_stock_pct < config.min_stock_pct:
                return GuardrailDecision(
                    allowed=False,
                    reason=f"Post-trade allocation {post_stock_pct:.2%} would be below min {config.min_stock_pct:.2%}",
                )

            if qty_to_sell <= 0:
                return GuardrailDecision(
                    allowed=False, reason="Calculated sell quantity is zero or negative"
                )

            return GuardrailDecision(
                allowed=True,
                reason=f"Sell approved: {qty_to_sell:.4f} shares to reach {target_stock_pct:.2%} allocation",
                trade_intent=TradeIntent(
                    side="sell", qty=qty_to_sell, reason=trigger_decision.reason
                ),
            )

    @staticmethod
    def validate_after_fill(
        position_state: PositionState,
        side: str,
        fill_qty: Decimal,
        price: Decimal,
        commission: Decimal,
        config: GuardrailConfig,
    ) -> tuple[bool, str | None]:
        """
        Validate if a proposed fill would result in a state that respects guardrails.

        This is a pure validation function used after order execution to ensure
        the resulting position state is within guardrail bounds.

        Returns:
            (is_valid, reason_if_invalid)
            - is_valid: True if allocation would be within bounds, False otherwise
            - reason_if_invalid: None if valid, error message if invalid
        """
        # Calculate post-fill state
        dq = fill_qty if side == "BUY" else -fill_qty
        new_qty = position_state.qty + dq

        # Calculate cash change
        if side == "BUY":
            cash_delta = -(fill_qty * price) - commission
        else:  # SELL
            cash_delta = (fill_qty * price) - commission

        new_cash = position_state.cash + cash_delta
        effective_cash = new_cash + position_state.dividend_receivable

        # Reject trades that would result in negative cash
        if new_cash < 0:
            return (
                False,
                f"Trade would result in negative cash (${float(new_cash):.2f}) - insufficient funds",
            )

        # Calculate allocation (stock % = stock_value / total_value)
        # Total value = stock value + cash (cash lives in PositionCell)
        stock_val = max(new_qty, Decimal("0")) * price
        total_val = stock_val + effective_cash

        # No capital → reject trade (cannot validate allocation without capital)
        if total_val <= 0:
            return False, "No capital available - cannot validate guardrails"

        alloc = stock_val / total_val

        # Strictly enforce guardrails: stock allocation must be within [min_stock_pct, max_stock_pct]
        # This ensures position trades only occur within the allowed cash/stock percentage bounds
        if config.min_stock_pct is not None and alloc < config.min_stock_pct:
            return (
                False,
                f"Stock allocation {alloc:.1%} would be below minimum {config.min_stock_pct:.1%} (violates guardrails)",
            )
        if config.max_stock_pct is not None and alloc > config.max_stock_pct:
            return (
                False,
                f"Stock allocation {alloc:.1%} would exceed maximum {config.max_stock_pct:.1%} (violates guardrails)",
            )

        return True, None

# =========================
# backend/application/use_cases/evaluate_position_uc.py
# =========================
from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, Callable
import logging
from decimal import Decimal
from datetime import datetime

from domain.ports.positions_repo import PositionsRepo
from domain.ports.portfolio_repo import PortfolioRepo
from domain.ports.events_repo import EventsRepo
from domain.ports.market_data import MarketDataRepo
from domain.ports.evaluation_timeline_repo import EvaluationTimelineRepo
from domain.ports.config_repo import ConfigRepo
from domain.entities.event import Event
from domain.services.price_trigger import PriceTrigger
from domain.value_objects.configs import TriggerConfig, GuardrailConfig, OrderPolicyConfig
from infrastructure.time.clock import Clock
from infrastructure.adapters.converters import (
    order_policy_to_trigger_config,
    guardrail_policy_to_guardrail_config,
)
from uuid import uuid4


class EvaluatePositionUC:
    """Advanced volatility trading evaluation with order sizing and guardrails."""
    _logger = logging.getLogger(__name__)

    def __init__(
        self,
        positions: PositionsRepo,
        events: EventsRepo,
        market_data: MarketDataRepo,
        clock: Clock,
        trigger_config_provider: Optional[
            Callable[[str, str, str], TriggerConfig]
        ] = None,
        guardrail_config_provider: Optional[
            Callable[[str, str, str], GuardrailConfig]
        ] = None,
        order_policy_config_provider: Optional[
            Callable[[str, str, str], OrderPolicyConfig]
        ] = None,
        config_repo: Optional[ConfigRepo] = None,
        portfolio_repo: Optional[PortfolioRepo] = None,
        evaluation_timeline_repo: Optional[EvaluationTimelineRepo] = None,
    ) -> None:
        self.positions = positions
        self.events = events
        self.market_data = market_data
        self.clock = clock
        # Config providers - if None, will fall back to extracting from Position entity (backward compat)
        self.trigger_config_provider = trigger_config_provider
        self.guardrail_config_provider = guardrail_config_provider
        self.order_policy_config_provider = order_policy_config_provider
        self.config_repo = config_repo  # For getting commission_rate
        self.portfolio_repo = portfolio_repo
        self.evaluation_timeline_repo = evaluation_timeline_repo

    @staticmethod
    def _derive_action_for_timeline(
        trigger_result: Dict[str, Any],
        order_proposal: Optional[Dict[str, Any]],
    ) -> str:
        if not trigger_result.get("triggered"):
            return "HOLD"
        if not order_proposal:
            return "SKIP"
        validation = order_proposal.get("validation")
        if validation is not None and not validation.get("valid", True):
            return "SKIP"
        side = trigger_result.get("side")
        if side == "BUY":
            return "BUY"
        if side == "SELL":
            return "SELL"
        return "SKIP"

    def evaluate(
        self,
        tenant_id: str,
        portfolio_id: str,
        position_id: str,
        current_price: float,
        write_timeline: bool = True,
    ) -> Dict[str, Any]:
        """Evaluate position for volatility triggers with complete order sizing."""

        # Get position
        position = self.positions.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            raise KeyError("position_not_found")

        # Cash lives in Position entity (cash lives in PositionCell per target state model)
        # No need to fetch portfolio_cash separately

        # Check if we have an anchor price
        if not position.anchor_price:
            return {
                "position_id": position_id,
                "current_price": current_price,
                "anchor_price": None,
                "trigger_detected": False,
                "reasoning": "No anchor price set - cannot evaluate triggers",
            }

        # Check for anchor price anomaly (e.g., >50% difference suggests incorrect anchor)
        # If anchor is clearly wrong, reset it to current market price
        anchor_reset_info = self._check_and_reset_anchor_if_anomalous(
            tenant_id, portfolio_id, position, current_price
        )

        # Check triggers
        trigger_result = self._check_triggers(tenant_id, portfolio_id, position, current_price)

        # Check for auto-rebalancing needs (if no trigger detected)
        rebalance_proposal = None
        if not trigger_result["triggered"]:
            rebalance_proposal = self._check_auto_rebalancing(
                tenant_id, portfolio_id, position, current_price
            )
            if rebalance_proposal:
                trigger_result["triggered"] = True
                trigger_result["side"] = rebalance_proposal["side"]
                trigger_result["reasoning"] = rebalance_proposal["reasoning"]
                trigger_result["order_proposal"] = rebalance_proposal

        # If trigger detected, calculate order size and validate
        order_proposal = None
        if trigger_result["triggered"] and not rebalance_proposal:
            order_proposal = self._calculate_order_proposal(
                tenant_id,
                portfolio_id,
                position,
                current_price,
                trigger_result["side"],
                price_timestamp=self.clock.now(),
            )
            trigger_result["order_proposal"] = order_proposal

        # Log event
        self._log_evaluation_event(tenant_id, portfolio_id, position, current_price, trigger_result)

        # Calculate delta_pct for debugging/display
        delta_pct = 0.0
        if position.anchor_price and float(position.anchor_price) > 0:
            anchor_float = float(position.anchor_price)
            current_price_float = float(current_price)
            delta_pct = ((current_price_float - anchor_float) / anchor_float) * 100

        result = {
            "position_id": position_id,
            "current_price": current_price,
            "anchor_price": position.anchor_price,
            "delta_pct": delta_pct,
            "trigger_detected": trigger_result["triggered"],
            "trigger_type": trigger_result.get("side"),
            "order_proposal": order_proposal,
            "reasoning": trigger_result["reasoning"],
        }

        # Add anchor reset info if anchor was reset
        if anchor_reset_info:
            result["anchor_reset"] = anchor_reset_info

        timeline_record_id = None
        if write_timeline:
            # Write to canonical PositionEvaluationTimeline table (ONE ROW PER EVALUATION)
            # Create minimal price_data for timeline (evaluate method doesn't have full market data)
            from domain.entities.market_data import PriceData, PriceSource

            minimal_price_data = PriceData(
                ticker=position.asset_symbol,
                price=current_price,
                source=PriceSource.LAST_TRADE,  # Use LAST_TRADE as default for manual evaluation
                timestamp=self.clock.now(),
                is_market_hours=True,  # Assume market hours for manual evaluation
                is_fresh=True,
                is_inline=True,
            )

            # Create minimal validation result
            validation = {"valid": True, "rejections": [], "warnings": []}

            # Get portfolio for trading_hours_policy
            portfolio = None
            if self.portfolio_repo:
                portfolio = self.portfolio_repo.get(
                    tenant_id=tenant_id, portfolio_id=portfolio_id
                )

            timeline_record_id = self._write_timeline_row(
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                position=position,
                price_data=minimal_price_data,
                validation=validation,
                allow_after_hours=(
                    position.order_policy.allow_after_hours if position.order_policy else False
                ),
                trading_hours_policy=portfolio.trading_hours_policy if portfolio else None,
                anchor_reset_info=anchor_reset_info,
                trigger_result=trigger_result,
                order_proposal=order_proposal or rebalance_proposal,
                action=self._derive_action_for_timeline(
                    trigger_result, order_proposal or rebalance_proposal
                ),
                source="api/manual",  # Manual evaluation
            )

        if timeline_record_id:
            result["timeline_record_id"] = timeline_record_id

        return result

    def evaluate_with_market_data(
        self, tenant_id: str, portfolio_id: str, position_id: str
    ) -> Dict[str, Any]:
        """Evaluate position using real-time market data with after-hours support."""

        # Get position
        position = self.positions.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            raise KeyError("position_not_found")

        # Cash lives in Position entity (cash lives in PositionCell per target state model)
        # No need to fetch portfolio_cash separately

        # Check if we have an anchor price
        if not position.anchor_price:
            return {
                "position_id": position_id,
                "current_price": None,
                "anchor_price": None,
                "trigger_detected": False,
                "reasoning": "No anchor price set - cannot evaluate triggers",
                "market_data": None,
            }

        # Get real-time market data
        price_data = self.market_data.get_reference_price(position.asset_symbol)
        if not price_data:
            return {
                "position_id": position_id,
                "current_price": None,
                "anchor_price": position.anchor_price,
                "trigger_detected": False,
                "reasoning": "Unable to fetch market data",
                "market_data": None,
            }

        # Determine allow_after_hours:
        # - Portfolio-level trading_hours_policy is the primary control:
        #   OPEN_ONLY  -> no after-hours
        #   OPEN_PLUS_AFTER_HOURS -> after-hours allowed
        # - Per-position OrderPolicy can further restrict (but not override OPEN_ONLY)
        allow_after_hours: bool = position.order_policy.allow_after_hours

        # Apply config store override if available
        if self.order_policy_config_provider:
            order_policy_config = self.order_policy_config_provider(
                tenant_id, portfolio_id, position_id
            )
            if order_policy_config is not None:
                allow_after_hours = order_policy_config.allow_after_hours

        # Apply portfolio-level trading_hours_policy if portfolio_repo is available
        if self.portfolio_repo is not None:
            portfolio = self.portfolio_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)
            if portfolio is not None:
                if portfolio.trading_hours_policy == "OPEN_ONLY":
                    # Master off switch – force after-hours off
                    allow_after_hours = False
                elif portfolio.trading_hours_policy == "OPEN_PLUS_AFTER_HOURS":
                    # Master on switch – enable after-hours regardless of per-position flag
                    allow_after_hours = True

        # Validate price data with after-hours setting
        validation = self.market_data.validate_price(
            price_data, allow_after_hours=allow_after_hours
        )

        # If validation fails, return early
        if not validation["valid"]:
            return {
                "position_id": position_id,
                "current_price": price_data.price,
                "anchor_price": position.anchor_price,
                "trigger_detected": False,
                "reasoning": f"Market data validation failed: {', '.join(validation['rejections'])}",
                "market_data": {
                    "price": price_data.price,
                    "source": price_data.source.value,
                    "timestamp": price_data.timestamp.isoformat(),
                    "is_market_hours": price_data.is_market_hours,
                    "validation": validation,
                },
            }

        # Check for anchor price anomaly and auto-reset if needed
        anchor_reset_info = self._check_and_reset_anchor_if_anomalous(
            tenant_id, portfolio_id, position, price_data.price
        )

        # Check triggers with real market price
        trigger_result = self._check_triggers(tenant_id, portfolio_id, position, price_data.price)

        # Check for auto-rebalancing needs (if no trigger detected)
        rebalance_proposal = None
        if not trigger_result["triggered"]:
            rebalance_proposal = self._check_auto_rebalancing(
                tenant_id, portfolio_id, position, price_data.price
            )
            if rebalance_proposal:
                trigger_result["triggered"] = True
                trigger_result["side"] = rebalance_proposal["side"]
                trigger_result["reasoning"] = rebalance_proposal["reasoning"]
                trigger_result["order_proposal"] = rebalance_proposal

        # If trigger detected, calculate order size and validate
        order_proposal = None
        if trigger_result["triggered"] and not rebalance_proposal:
            order_proposal = self._calculate_order_proposal(
                tenant_id,
                portfolio_id,
                position,
                price_data.price,
                trigger_result["side"],
                price_timestamp=price_data.timestamp,
            )
            trigger_result["order_proposal"] = order_proposal

        # Log event
        self._log_evaluation_event(
            tenant_id, portfolio_id, position, price_data.price, trigger_result
        )

        result = {
            "position_id": position_id,
            "current_price": price_data.price,
            "anchor_price": position.anchor_price,
            "trigger_detected": trigger_result["triggered"],
            "trigger_type": trigger_result.get("side"),
            "order_proposal": order_proposal,
            "reasoning": trigger_result["reasoning"],
            "market_data": {
                "price": price_data.price,
                "source": price_data.source.value,
                "timestamp": price_data.timestamp.isoformat(),
                "bid": price_data.bid,
                "ask": price_data.ask,
                "volume": price_data.volume,
                "is_market_hours": price_data.is_market_hours,
                "is_fresh": price_data.is_fresh,
                "is_inline": price_data.is_inline,
                "validation": validation,
            },
        }

        # Add anchor reset info if anchor was reset
        if anchor_reset_info:
            result["anchor_reset"] = anchor_reset_info

        # Write to canonical PositionEvaluationTimeline table (ONE ROW PER EVALUATION)
        self._write_timeline_row(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position=position,
            price_data=price_data,
            validation=validation,
            allow_after_hours=allow_after_hours,
            trading_hours_policy=portfolio.trading_hours_policy if portfolio else None,
            anchor_reset_info=anchor_reset_info,
            trigger_result=trigger_result,
            order_proposal=order_proposal or rebalance_proposal,
            action=self._derive_action_for_timeline(
                trigger_result, order_proposal or rebalance_proposal
            ),
            source="api/manual",  # TODO: Pass source from caller
        )

        return result

    def _check_and_reset_anchor_if_anomalous(
        self, tenant_id: str, portfolio_id: str, position, current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if anchor price is clearly wrong (e.g., >50% difference from market).
        If so, reset anchor to current market price and log an event.

        Returns anchor reset info if reset occurred, None otherwise.
        """
        if not position.anchor_price or position.anchor_price <= 0:
            return None

        # Calculate percentage difference
        # Convert both to float to avoid Decimal/float type mismatch
        anchor_price_float = float(position.anchor_price) if position.anchor_price else 0.0
        current_price_float = float(current_price)
        price_diff_pct = abs((current_price_float - anchor_price_float) / anchor_price_float) * 100

        # Threshold: if anchor differs by >50% from market, it's likely wrong
        # This handles cases like anchor=$50, market=$21 (58% difference)
        ANOMALY_THRESHOLD_PCT = 50.0

        if price_diff_pct > ANOMALY_THRESHOLD_PCT:
            old_anchor = position.anchor_price
            new_anchor = current_price

            # Reset anchor to current market price
            position.set_anchor_price(new_anchor)
            self.positions.save(position)  # Position is already scoped to tenant_id+portfolio_id

            # Log event
            event = Event(
                id=f"evt_anchor_reset_{position.id}_{uuid4().hex[:8]}",
                position_id=position.id,
                type="anchor_price_auto_reset",
                inputs={
                    "old_anchor_price": old_anchor,
                    "current_market_price": current_price,
                    "price_difference_pct": price_diff_pct,
                    "threshold_pct": ANOMALY_THRESHOLD_PCT,
                },
                outputs={
                    "new_anchor_price": new_anchor,
                    "reason": f"Anchor price differed by {price_diff_pct:.1f}% from market (threshold: {ANOMALY_THRESHOLD_PCT}%)",
                },
                message=f"Auto-reset anchor from ${old_anchor:.2f} to ${new_anchor:.2f} (market price) due to {price_diff_pct:.1f}% difference",
                ts=self.clock.now(),
            )
            self.events.append(event)

            self._logger.warning(
                "Anchor price anomaly detected for %s: $%.2f -> $%.2f (%.1f%% difference). Auto-reset to market price.",
                position.asset_symbol,
                old_anchor,
                new_anchor,
                price_diff_pct,
            )

            return {
                "reset": True,
                "old_anchor_price": old_anchor,
                "new_anchor_price": new_anchor,
                "price_difference_pct": price_diff_pct,
                "reason": f"Anchor differed by {price_diff_pct:.1f}% from market price",
            }

        return None

    def _check_triggers(
        self, tenant_id: str, portfolio_id: str, position, current_price: float
    ) -> Dict[str, Any]:
        """Check if current price triggers buy or sell using domain service."""
        # Get trigger config from provider or fall back to extracting from Position (backward compat)
        if self.trigger_config_provider:
            trigger_config = self.trigger_config_provider(tenant_id, portfolio_id, position.id)
        else:
            # Fallback: extract from Position entity (for backward compatibility)
            trigger_config = order_policy_to_trigger_config(position.order_policy)

        # Use domain service for trigger evaluation
        anchor_decimal = Decimal(str(position.anchor_price)) if position.anchor_price else None
        current_price_decimal = Decimal(str(current_price))

        trigger_decision = PriceTrigger.evaluate(
            anchor_price=anchor_decimal,
            current_price=current_price_decimal,
            config=trigger_config,
        )

        # Convert domain decision to legacy format
        if trigger_decision.fired:
            # Convert direction from "buy"/"sell" to "BUY"/"SELL"
            side = trigger_decision.direction.upper() if trigger_decision.direction else None
            return {
                "triggered": True,
                "side": side,
                "reasoning": trigger_decision.reason or f"Trigger fired: {side}",
            }
        else:
            return {
                "triggered": False,
                "reasoning": trigger_decision.reason
                or f"Price ${current_price:.2f} within threshold range",
            }

    def _calculate_order_proposal(
        self,
        tenant_id: str,
        portfolio_id: str,
        position,
        current_price: float,
        side: str,
        price_timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Calculate order size using the specification formula with guardrail trimming."""

        # Get configs from provider or fall back to extracting from Position (backward compat)
        if self.trigger_config_provider:
            trigger_config = self.trigger_config_provider(tenant_id, portfolio_id, position.id)
        else:
            # Fallback: extract from Position entity (for backward compatibility)
            trigger_config = order_policy_to_trigger_config(position.order_policy)

        if self.guardrail_config_provider:
            guardrail_config = self.guardrail_config_provider(tenant_id, portfolio_id, position.id)
        else:
            # Fallback: extract from Position entity (for backward compatibility)
            guardrail_config = guardrail_policy_to_guardrail_config(position.guardrails)

        if self.order_policy_config_provider:
            order_policy_config = self.order_policy_config_provider(
                tenant_id, portfolio_id, position.id
            )
            rebalance_ratio = (
                float(order_policy_config.rebalance_ratio)
                if order_policy_config
                else position.order_policy.rebalance_ratio
            )
        else:
            # Fallback: extract from Position entity (for backward compatibility)
            order_policy_config = None
            rebalance_ratio = position.order_policy.rebalance_ratio

        # Get commission_rate from ConfigRepo (preferred) or fallback to position
        if self.config_repo:
            commission_rate = self.config_repo.get_commission_rate(
                tenant_id=tenant_id,
                asset_id=position.asset_symbol,  # Use asset_symbol instead of ticker
            )
        else:
            commission_rate = position.order_policy.commission_rate

        # Apply order sizing formula: ΔQ_raw = (P_anchor / P - 1) × r × ((A + C) / P)
        # Calculate portfolio values
        # Convert to float to avoid Decimal/float type mismatch
        current_price_float = float(current_price)
        asset_value = position.qty * current_price_float
        total_value = asset_value + position.cash  # Cash lives in PositionCell

        anchor = position.anchor_price
        anchor_float = float(anchor) if anchor else 0.0

        raw_qty = (
            (anchor_float / current_price_float - 1)
            * rebalance_ratio
            * (total_value / current_price_float)
        )

        # The formula produces:
        # - Negative qty when anchor < current (price went up = sell signal)
        # - Positive qty when anchor > current (price went down = buy signal)
        # For SELL orders, we need to ensure it's negative
        # For BUY orders, we need to ensure it's positive

        if side == "SELL":
            # For SELL, ensure negative (if formula gave positive, negate it)
            if raw_qty > 0:
                raw_qty = -raw_qty
            # CRITICAL SAFETY CHECKS:
            # 1. Never sell more than available shares
            max_sellable = position.qty
            if abs(raw_qty) > max_sellable:
                self._logger.debug(
                    "Order sizing capped sell qty=%.2f to available=%.2f shares.",
                    abs(raw_qty),
                    max_sellable,
                )
                raw_qty = -max_sellable
            # 2. Never sell more than max_trade_pct_of_position if configured
            max_pct = (
                float(guardrail_config.max_trade_pct_of_position)
                if guardrail_config.max_trade_pct_of_position
                else 1.0
            )
            max_trade_notional = total_value * max_pct
            max_trade_qty = max_trade_notional / current_price_float
            max_pct_sellable = min(position.qty, max_trade_qty)
            if abs(raw_qty) > max_pct_sellable:
                self._logger.debug(
                    "Order sizing capped sell qty=%.2f to max_per_trade=%.2f (%.1f%% of %.2f shares).",
                    abs(raw_qty),
                    max_pct_sellable,
                    max_pct * 100,
                    position.qty,
                )
                raw_qty = -max_pct_sellable
        else:  # BUY
            # For BUY, ensure positive (if formula gave negative, make it positive)
            if raw_qty < 0:
                raw_qty = -raw_qty
            # CRITICAL SAFETY CHECK: Never use more than max_trade_pct_of_position of cash if configured
            max_pct = (
                float(guardrail_config.max_trade_pct_of_position)
                if guardrail_config.max_trade_pct_of_position
                else 1.0
            )
            max_trade_notional = total_value * max_pct
            max_buy_notional = min(position.cash, max_trade_notional)
            max_buy_qty = max_buy_notional / float(current_price)
            if raw_qty > max_buy_qty:
                self._logger.debug(
                    "Order sizing capped buy qty=%.2f to max_per_trade=%.2f (%.1f%% of $%.2f cash).",
                    raw_qty,
                    max_buy_qty,
                    max_pct * 100,
                    position.cash,
                )
                raw_qty = max_buy_qty

        # Apply guardrail trimming
        # Convert to float to avoid Decimal/float type mismatch
        current_price_float = float(current_price)
        trimmed_qty, trimming_reason = self._apply_guardrail_trimming(
            tenant_id,
            portfolio_id,
            position,
            raw_qty,
            current_price_float,
            side,
            guardrail_config,
        )

        # Calculate order details
        notional = abs(trimmed_qty) * current_price_float
        # Use commission_rate from order_policy_config or fallback to position
        commission = notional * commission_rate

        # Validate order
        validation_result = self._validate_order(
            tenant_id,
            portfolio_id,
            position,
            trimmed_qty,
            current_price_float,
            side,
            notional,
            commission,
            price_timestamp=price_timestamp,
        )

        return {
            "side": side,
            "raw_qty": raw_qty,
            "trimmed_qty": trimmed_qty,
            "notional": notional,
            "commission": commission,
            "trimming_reason": trimming_reason,
            "validation": validation_result,
            "post_trade_asset_pct": self._calculate_post_trade_allocation(
                position, trimmed_qty, float(current_price)
            ),
        }

    def _apply_guardrail_trimming(
        self,
        tenant_id: str,
        portfolio_id: str,
        position,
        raw_qty: float,
        current_price: float,
        side: str,
        guardrail_config: GuardrailConfig,
    ) -> Tuple[float, str]:
        """Apply guardrail trimming to ensure Asset% within guardrail bounds post-trade."""

        # CRITICAL: For SELL orders, never sell more than available shares
        if side == "SELL" and raw_qty < 0:
            max_sellable = position.qty
            if abs(raw_qty) > max_sellable:
                self._logger.debug(
                    "Raw sell qty %.2f exceeds available %.2f; capping to available.",
                    abs(raw_qty),
                    max_sellable,
                )
                raw_qty = -max_sellable  # Cap to maximum sellable (negative for sell)

        # Get commission_rate from ConfigRepo (preferred) or fallback to position
        if self.config_repo:
            commission_rate_for_calc = self.config_repo.get_commission_rate(
                tenant_id=tenant_id,
                asset_id=position.asset_symbol,  # Use asset_symbol instead of ticker
            )
        else:
            commission_rate_for_calc = position.order_policy.commission_rate

        # Calculate post-trade allocation without trimming
        # Convert to float to avoid Decimal/float type mismatch
        current_price_float = float(current_price)
        post_qty = position.qty + raw_qty
        post_asset_value = post_qty * current_price_float
        # Calculate post-trade cash from position.cash (cash lives in PositionCell)
        cash_delta = -(raw_qty * current_price_float) - (  # Negative for BUY, positive for SELL
            abs(raw_qty) * current_price_float * commission_rate_for_calc
        )  # Always subtract commission
        post_cash = position.cash + cash_delta  # Cash lives in PositionCell
        post_total_value = post_asset_value + post_cash
        post_asset_pct = post_asset_value / post_total_value if post_total_value > 0 else 0

        # Check if trimming is needed using guardrail config
        min_alloc = float(guardrail_config.min_stock_pct)
        max_alloc = float(guardrail_config.max_stock_pct)

        if post_asset_pct < min_alloc:
            # Need to buy more to reach minimum allocation
            target_asset_value = min_alloc * post_total_value
            target_qty = target_asset_value / current_price
            trimmed_qty = target_qty - position.qty
            reason = (
                f"Trimmed to reach minimum allocation {min_alloc:.1%} (was {post_asset_pct:.1%})"
            )
        elif post_asset_pct > max_alloc:
            # Need to sell more to reach maximum allocation
            target_asset_value = max_alloc * post_total_value
            target_qty = target_asset_value / current_price
            trimmed_qty = target_qty - position.qty

            # CRITICAL: For SELL orders, apply all limits in order:
            # 1. Never exceed available shares
            # 2. Never exceed max_trade_pct_of_position if configured
            if trimmed_qty < 0:  # Negative means sell
                max_sellable = position.qty
                max_pct = (
                    float(guardrail_config.max_trade_pct_of_position)
                    if guardrail_config.max_trade_pct_of_position
                    else 1.0
                )
                total_value = (position.qty * current_price_float) + position.cash
                max_trade_notional = total_value * max_pct
                max_pct_sellable = min(max_sellable, max_trade_notional / current_price_float)
                # Apply both limits - take the minimum (most restrictive)
                max_allowed = min(max_sellable, max_pct_sellable)

                if abs(trimmed_qty) > max_allowed:
                    self._logger.debug(
                        "Trimmed sell qty %.2f exceeds limit %.2f (available %.2f, max_pct %.2f); capping.",
                        abs(trimmed_qty),
                        max_allowed,
                        max_sellable,
                        max_pct_sellable,
                    )
                    trimmed_qty = -max_allowed
                    reason = (
                        f"Trimmed to max allocation {max_alloc:.1%} but capped to {max_allowed:.2f} shares "
                        f"(max {max_pct:.1%} per trade)"
                    )
                else:
                    reason = f"Trimmed to reach maximum allocation {max_alloc:.1%} (was {post_asset_pct:.1%})"
            else:
                reason = f"Trimmed to reach maximum allocation {max_alloc:.1%} (was {post_asset_pct:.1%})"
        else:
            # No trimming needed, but still check per-trade limits
            trimmed_qty = raw_qty
            max_pct = (
                float(guardrail_config.max_trade_pct_of_position)
                if guardrail_config.max_trade_pct_of_position
                else 1.0
            )
            if side == "SELL" and trimmed_qty < 0:
                max_sellable = position.qty
                total_value = (position.qty * current_price_float) + position.cash
                max_trade_notional = total_value * max_pct
                max_pct_sellable = min(max_sellable, max_trade_notional / current_price_float)
                max_allowed = min(max_sellable, max_pct_sellable)

                if abs(trimmed_qty) > max_allowed:
                    self._logger.debug(
                        "Raw sell qty %.2f exceeds limit %.2f; capping to limit.",
                        abs(trimmed_qty),
                        max_allowed,
                    )
                    trimmed_qty = -max_allowed
                    reason = f"Capped to {max_allowed:.2f} shares (max {max_pct:.1%} per trade, raw was {abs(raw_qty):.2f})"
                else:
                    reason = "No trimming needed - within guardrail bounds"
            elif side == "BUY" and trimmed_qty > 0:
                total_value = (position.qty * current_price_float) + position.cash
                max_trade_notional = total_value * max_pct
                max_buy_notional = min(position.cash, max_trade_notional)
                max_buy_qty = max_buy_notional / current_price

                if trimmed_qty > max_buy_qty:
                    self._logger.debug(
                        "Raw buy qty %.2f exceeds limit %.2f; capping to limit.",
                        trimmed_qty,
                        max_buy_qty,
                    )
                    trimmed_qty = max_buy_qty
                    reason = f"Capped to {max_buy_qty:.2f} shares (max {max_pct:.1%} of cash per trade, raw was {raw_qty:.2f})"
                else:
                    reason = "No trimming needed - within guardrail bounds"
            else:
                reason = "No trimming needed - within guardrail bounds"

        return trimmed_qty, reason

    def _check_auto_rebalancing(
        self, tenant_id: str, portfolio_id: str, position, current_price: float
    ) -> Optional[Dict[str, Any]]:
        """Check if position needs auto-rebalancing due to drift outside guardrails."""

        # Get guardrail config from provider or fall back to extracting from Position (backward compat)
        if self.guardrail_config_provider:
            guardrail_config = self.guardrail_config_provider(tenant_id, portfolio_id, position.id)
        else:
            # Fallback: extract from Position entity (for backward compatibility)
            guardrail_config = guardrail_policy_to_guardrail_config(position.guardrails)

        # Get commission_rate from ConfigRepo (preferred) or fallback to position
        if self.config_repo:
            commission_rate = self.config_repo.get_commission_rate(
                tenant_id=tenant_id,
                asset_id=position.asset_symbol,  # Use asset_symbol instead of ticker
            )
        else:
            commission_rate = position.order_policy.commission_rate

        # Calculate current allocation
        # Convert to float to avoid Decimal/float type mismatch
        current_price_float = float(current_price)
        current_asset_value = position.qty * current_price_float
        current_total_value = current_asset_value + position.cash  # Cash lives in PositionCell
        current_asset_pct = (
            current_asset_value / current_total_value if current_total_value > 0 else 0
        )

        min_alloc = float(guardrail_config.min_stock_pct)
        max_alloc = float(guardrail_config.max_stock_pct)

        # Check if we're outside guardrails
        if current_asset_pct < min_alloc:
            # Need to buy to reach minimum allocation
            # Convert to float to avoid Decimal/float type mismatch
            current_price_float = float(current_price)
            target_asset_value = min_alloc * current_total_value
            target_qty = target_asset_value / current_price_float
            rebalance_qty = target_qty - position.qty

            if rebalance_qty > 0.001:  # Only rebalance if significant
                notional = rebalance_qty * current_price_float
                commission = rebalance_qty * current_price_float * commission_rate
                return {
                    "side": "BUY",
                    "reasoning": f"Auto-rebalance: Asset allocation {current_asset_pct:.1%} below minimum {min_alloc:.1%}",
                    "raw_qty": rebalance_qty,
                    "trimmed_qty": rebalance_qty,
                    "notional": notional,
                    "commission": commission,
                    "trimming_reason": "Auto-rebalance to minimum allocation",
                    "validation": self._validate_order(
                        tenant_id,
                        portfolio_id,
                        position,
                        rebalance_qty,
                        current_price_float,
                        "BUY",
                        notional,
                        commission,
                    ),
                    "post_trade_asset_pct": min_alloc,
                }

        elif current_asset_pct > max_alloc:
            # Need to sell to reach maximum allocation
            # Convert to float to avoid Decimal/float type mismatch
            current_price_float = float(current_price)
            target_asset_value = max_alloc * current_total_value
            target_qty = target_asset_value / current_price_float
            rebalance_qty = target_qty - position.qty

            if rebalance_qty < -0.001:  # Only rebalance if significant
                abs_qty = abs(rebalance_qty)
                notional = abs_qty * current_price_float
                commission = abs_qty * current_price_float * commission_rate
                return {
                    "side": "SELL",
                    "reasoning": f"Auto-rebalance: Asset allocation {current_asset_pct:.1%} above maximum {max_alloc:.1%}",
                    "raw_qty": rebalance_qty,
                    "trimmed_qty": rebalance_qty,
                    "notional": notional,
                    "commission": commission,
                    "trimming_reason": "Auto-rebalance to maximum allocation",
                    "validation": self._validate_order(
                        tenant_id,
                        portfolio_id,
                        position,
                        rebalance_qty,
                        current_price_float,
                        "SELL",
                        notional,
                        commission,
                    ),
                    "post_trade_asset_pct": max_alloc,
                }

        return None

    def _validate_order(
        self,
        tenant_id: str,
        portfolio_id: str,
        position,
        qty: float,
        price: float,
        side: str,
        notional: float,
        commission: float,
        price_timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Validate order against business rules including market hours and duplicates."""

        validation_result = {"valid": True, "rejections": [], "warnings": []}

        # Get min_notional from order_policy_config or fallback to position
        if self.order_policy_config_provider:
            order_policy_config = self.order_policy_config_provider(
                tenant_id, portfolio_id, position.id
            )
            min_notional = (
                float(order_policy_config.min_notional)
                if order_policy_config
                else position.order_policy.min_notional
            )
        else:
            min_notional = position.order_policy.min_notional

        # Check minimum notional
        if notional < min_notional:
            validation_result["valid"] = False
            validation_result["rejections"].append(
                f"Notional ${notional:.2f} below minimum ${min_notional:.2f}"
            )

        # Check sufficient cash for buy orders
        if side == "BUY":
            required_cash = (qty * price) + commission
            if required_cash > position.cash:  # Cash lives in PositionCell
                validation_result["valid"] = False
                validation_result["rejections"].append(
                    f"Insufficient cash: need ${required_cash:.2f}, have ${position.cash:.2f}"
                )

        # Check sufficient shares for sell orders
        if side == "SELL":
            if abs(qty) > position.qty:
                validation_result["valid"] = False
                validation_result["rejections"].append(
                    f"Insufficient shares: trying to sell {abs(qty):.2f}, have {position.qty:.2f}"
                )

        # Check for zero quantity
        if abs(qty) < 0.001:  # Less than 0.001 shares
            validation_result["valid"] = False
            validation_result["rejections"].append(
                "Order quantity too small (less than 0.001 shares)"
            )

        # Determine allow_after_hours (same logic as evaluate_with_market_data)
        # - Portfolio-level trading_hours_policy is the primary control
        allow_after_hours: bool = position.order_policy.allow_after_hours

        # Apply config store override if available
        if self.order_policy_config_provider:
            order_policy_config = self.order_policy_config_provider(
                tenant_id, portfolio_id, position.id
            )
            if order_policy_config is not None:
                allow_after_hours = order_policy_config.allow_after_hours

        # Apply portfolio-level trading_hours_policy if portfolio_repo is available
        if self.portfolio_repo is not None:
            portfolio = self.portfolio_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)
            if portfolio is not None:
                if portfolio.trading_hours_policy == "OPEN_ONLY":
                    # Master off switch – force after-hours off
                    allow_after_hours = False
                elif portfolio.trading_hours_policy == "OPEN_PLUS_AFTER_HOURS":
                    # Master on switch – enable after-hours regardless of per-position flag
                    allow_after_hours = True

        # Check market hours (respect after-hours setting)
        if not self._is_market_hours(price_timestamp):
            if not allow_after_hours:
                validation_result["valid"] = False
                validation_result["rejections"].append(
                    "Market is closed - after-hours trading disabled"
                )
            else:
                validation_result["warnings"].append("Trading after market hours")

        # Check for duplicate orders (simplified - check if there's a recent order for this position)
        if self._has_recent_order(position.id):
            validation_result["valid"] = False
            validation_result["rejections"].append(
                "Duplicate order detected - recent order already exists for this position"
            )

        # Check daily order limit
        if self._exceeds_daily_limit(position.id):
            validation_result["valid"] = False
            validation_result["rejections"].append(
                f"Daily order limit exceeded (max {position.guardrails.max_orders_per_day} orders per day)"
            )

        return validation_result

    def _is_market_hours(self, timestamp: Optional[datetime] = None) -> bool:
        """Check if current time is during market hours (simplified implementation)."""
        now = timestamp or self.clock.now()

        # Convert to ET (simplified - assume UTC-5 for ET)
        et_hour = (now.hour - 5) % 24
        et_weekday = now.weekday()  # 0 = Monday, 6 = Sunday

        # Market hours: 9:30 AM to 4:00 PM ET, Monday-Friday
        if et_weekday >= 5:  # Weekend
            return False

        if et_hour < 9 or (et_hour == 9 and now.minute < 30):
            return False

        if et_hour >= 16:  # 4:00 PM or later
            return False

        return True

    def _has_recent_order(self, position_id: str) -> bool:
        """Check if there's a recent order for this position (simplified implementation)."""
        # In a real implementation, this would check the orders repository
        # For now, we'll return False to allow orders
        return False

    def _exceeds_daily_limit(self, position_id: str) -> bool:
        """Check if daily order limit has been exceeded (simplified implementation)."""
        # In a real implementation, this would check the orders repository for today's orders
        # For now, we'll return False to allow orders
        return False

    def _calculate_post_trade_allocation(self, position, qty: float, price: float) -> float:
        """Calculate asset allocation percentage after the proposed trade."""
        # Get commission_rate from ConfigRepo (preferred) or fallback to position
        # Note: tenant_id and portfolio_id not available here, but we can get from position
        if self.config_repo:
            commission_rate = self.config_repo.get_commission_rate(
                tenant_id=position.tenant_id,
                asset_id=position.asset_symbol,  # Use asset_symbol instead of ticker
            )
        else:
            commission_rate = position.order_policy.commission_rate

        # Convert to float to avoid Decimal/float type mismatch
        price_float = float(price)
        post_qty = position.qty + qty
        post_asset_value = post_qty * price_float
        # Calculate post-trade cash from position.cash (cash lives in PositionCell)
        cash_delta = -(qty * price_float) - (abs(qty) * price_float * commission_rate)
        post_cash = position.cash + cash_delta  # Cash lives in PositionCell
        post_total_value = post_asset_value + post_cash

        return post_asset_value / post_total_value if post_total_value > 0 else 0

    def _log_evaluation_event(
        self,
        tenant_id: str,
        portfolio_id: str,
        position,
        current_price: float,
        trigger_result: Dict[str, Any],
    ) -> None:
        """Log evaluation event with order proposal details."""

        # Cash lives in Position entity (cash lives in PositionCell per target state model)
        cash_balance = position.cash

        # Calculate current position metrics
        # Convert to float to avoid Decimal/float type mismatch
        current_price_float = float(current_price)
        current_market_value = position.qty * current_price_float
        current_total_value = cash_balance + current_market_value  # Use position.cash
        current_asset_pct = (
            (current_market_value / current_total_value * 100) if current_total_value > 0 else 0
        )

        # Calculate P&L if anchor price exists
        pnl = 0.0
        pnl_pct = 0.0
        price_change = 0.0
        price_change_pct = 0.0
        if position.anchor_price and position.anchor_price > 0:
            # Convert both to float to avoid Decimal/float type mismatch
            anchor_price_float = float(position.anchor_price)
            current_price_float = float(current_price)
            price_change = current_price_float - anchor_price_float
            price_change_pct = (price_change / anchor_price_float) * 100
            pnl = price_change * position.qty
            pnl_pct = price_change_pct

        # Try to get market data snapshot (OHLC)
        market_data_snapshot = {}
        try:
            price_data = self.market_data.get_price(
                position.asset_symbol
            )  # Use asset_symbol instead of ticker
            if price_data:
                market_data_snapshot = {
                    "price": price_data.price,
                    "open": price_data.open,
                    "high": price_data.high,
                    "low": price_data.low,
                    "close": price_data.close,
                    "volume": price_data.volume,
                    "bid": price_data.bid,
                    "ask": price_data.ask,
                    "timestamp": price_data.timestamp.isoformat() if price_data.timestamp else None,
                    "is_market_hours": price_data.is_market_hours,
                    "is_fresh": price_data.is_fresh,
                }
        except Exception as e:
            self._logger.warning("Could not get market data snapshot: %s", e)

        # Prepare inputs
        inputs = {
            "current_price": current_price,
            "anchor_price": position.anchor_price,
            "threshold_pct": (
                float(trigger_config.up_threshold_pct) / 100
                if self.trigger_config_provider
                and (
                    trigger_config := self.trigger_config_provider(
                        tenant_id, portfolio_id, position.id
                    )
                )
                else position.order_policy.trigger_threshold_pct
            ),
            "current_qty": position.qty,
            "current_cash": cash_balance,  # Cash lives in PositionCell
            "current_market_value": current_market_value,
            "current_total_value": current_total_value,
            "current_asset_pct": current_asset_pct,
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "market_data": market_data_snapshot,
        }

        # Prepare outputs
        outputs = {
            "trigger_detected": trigger_result["triggered"],
            "trigger_type": trigger_result.get("side"),
            "reasoning": trigger_result["reasoning"],
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "current_market_value": current_market_value,
            "current_total_value": current_total_value,
            "current_asset_pct": current_asset_pct,
        }

        # Add order proposal details if available
        if "order_proposal" in trigger_result and trigger_result["order_proposal"]:
            proposal = trigger_result["order_proposal"]
            inputs.update(
                {
                    "raw_qty": proposal["raw_qty"],
                    "rebalance_ratio": (
                        float(order_policy_config.rebalance_ratio)
                        if self.order_policy_config_provider
                        and (
                            order_policy_config := self.order_policy_config_provider(
                                tenant_id, portfolio_id, position.id
                            )
                        )
                        else position.order_policy.rebalance_ratio
                    ),
                }
            )
            outputs.update(
                {
                    "trimmed_qty": proposal["trimmed_qty"],
                    "notional": proposal["notional"],
                    "commission": proposal["commission"],
                    "trimming_reason": proposal["trimming_reason"],
                    "validation_valid": proposal["validation"]["valid"],
                    "post_trade_asset_pct": proposal["post_trade_asset_pct"],
                }
            )

            if proposal["validation"]["rejections"]:
                outputs["rejections"] = proposal["validation"]["rejections"]

        # Determine event type
        if trigger_result["triggered"]:
            event_type = "trigger_detected"
        else:
            event_type = "price_evaluation"  # Periodic check without trigger

        event = Event(
            id=f"evt_eval_{position.id}_{uuid4().hex[:8]}",
            position_id=position.id,
            type=event_type,
            inputs=inputs,
            outputs=outputs,
            message=trigger_result["reasoning"],
            ts=self.clock.now(),
        )
        self.events.append(event)

    def _write_timeline_row(
        self,
        tenant_id: str,
        portfolio_id: str,
        position,
        price_data,
        validation: Dict[str, Any],
        allow_after_hours: bool,
        trading_hours_policy: Optional[str],
        anchor_reset_info: Optional[Dict[str, Any]],
        trigger_result: Dict[str, Any],
        order_proposal: Optional[Dict[str, Any]],
        action: str,
        source: str = "api/manual",
        order_id: Optional[str] = None,
        trade_id: Optional[str] = None,
        execution_info: Optional[Dict[str, Any]] = None,
        position_qty_after: Optional[float] = None,
        position_cash_after: Optional[float] = None,
    ) -> Optional[str]:
        """
        Write a row to PositionEvaluationTimeline for this evaluation.

        This is called for EVERY evaluation, not just when trades occur.
        """
        if not self.evaluation_timeline_repo:
            return None  # Timeline repo not available

        try:
            from application.helpers.timeline_builder import build_timeline_row_from_evaluation

            # Get portfolio name
            portfolio_name = None
            if self.portfolio_repo:
                portfolio = self.portfolio_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)
                if portfolio:
                    portfolio_name = portfolio.name

            # Get configs for timeline
            trigger_config_dict = None
            guardrail_config_dict = None
            order_policy_dict = None

            if self.trigger_config_provider:
                trigger_config = self.trigger_config_provider(tenant_id, portfolio_id, position.id)
                if trigger_config:
                    trigger_config_dict = {
                        "up_threshold_pct": float(trigger_config.up_threshold_pct),
                        "down_threshold_pct": float(trigger_config.down_threshold_pct),
                    }

            if self.guardrail_config_provider:
                guardrail_config = self.guardrail_config_provider(
                    tenant_id, portfolio_id, position.id
                )
                if guardrail_config:
                    guardrail_config_dict = {
                        "min_stock_pct": (
                            float(guardrail_config.min_stock_pct)
                            if guardrail_config.min_stock_pct
                            else None
                        ),
                        "max_stock_pct": (
                            float(guardrail_config.max_stock_pct)
                            if guardrail_config.max_stock_pct
                            else None
                        ),
                        "max_trade_pct_of_position": (
                            float(guardrail_config.max_trade_pct_of_position)
                            if guardrail_config.max_trade_pct_of_position
                            else None
                        ),
                        "max_orders_per_day": guardrail_config.max_orders_per_day,
                    }

            if self.order_policy_config_provider:
                order_policy_config = self.order_policy_config_provider(
                    tenant_id, portfolio_id, position.id
                )
                if order_policy_config:
                    commission_rate = (
                        float(order_policy_config.commission_rate)
                        if order_policy_config.commission_rate is not None
                        else float(position.order_policy.commission_rate or 0.0)
                    )
                    order_policy_dict = {
                        "rebalance_ratio": float(order_policy_config.rebalance_ratio),
                        "commission_rate": commission_rate,
                        "min_qty": (
                            float(order_policy_config.min_qty)
                            if order_policy_config.min_qty
                            else None
                        ),
                        "min_notional": (
                            float(order_policy_config.min_notional)
                            if order_policy_config.min_notional
                            else None
                        ),
                    }

            # Build guardrail result dict
            guardrail_result_dict = None
            if order_proposal and "validation" in order_proposal:
                validation_result = order_proposal["validation"]
                guardrail_result_dict = {
                    "allowed": validation_result.get("valid", False),
                    "reason": (
                        ", ".join(validation_result.get("rejections", []))
                        if not validation_result.get("valid")
                        else None
                    ),
                }

            # Determine action reason - explicitly reference allocation when relevant
            action_reason = trigger_result.get("reasoning", "No trigger detected")

            # Calculate current allocation for action reason context
            # Convert price to float to avoid Decimal/float type mismatch
            price_float = float(price_data.price)
            current_stock_value = position.qty * price_float
            current_total_value = (position.cash or 0.0) + current_stock_value
            current_allocation_pct = (
                (current_stock_value / current_total_value * 100)
                if current_total_value > 0
                else 0.0
            )

            if order_proposal and "validation" in order_proposal:
                validation_result = order_proposal["validation"]
                if not validation_result.get("valid"):
                    rejections = validation_result.get("rejections", [])
                    # Enhance rejection messages to reference allocation if guardrail-related
                    enhanced_rejections = []
                    for rejection in rejections:
                        if "allocation" in rejection.lower() or "guardrail" in rejection.lower():
                            enhanced_rejections.append(
                                f"{rejection} (Current allocation: {current_allocation_pct:.1f}%)"
                            )
                        else:
                            enhanced_rejections.append(rejection)
                    action_reason = f"Trade blocked: {', '.join(enhanced_rejections)}"
                elif action in ("BUY", "SELL"):
                    # Include allocation context in action reason
                    post_trade_allocation = order_proposal.get("post_trade_asset_pct")
                    if post_trade_allocation is not None:
                        action_reason = (
                            f"{action} order proposed: {trigger_result.get('reasoning', 'Trigger fired')} "
                            f"(Allocation: {current_allocation_pct:.1f}% → {post_trade_allocation * 100:.1f}%)"
                        )
                    else:
                        action_reason = (
                            f"{action} order proposed: {trigger_result.get('reasoning', 'Trigger fired')} "
                            f"(Current allocation: {current_allocation_pct:.1f}%)"
                        )
            elif current_allocation_pct > 0:
                # Include allocation in HOLD/SKIP reasons for context
                action_reason = f"{action_reason} (Allocation: {current_allocation_pct:.1f}%)"

            # Build timeline row
            timeline_row = build_timeline_row_from_evaluation(
                mode="LIVE",
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                portfolio_name=portfolio_name,
                position_id=position.id,
                symbol=position.asset_symbol,
                timestamp=price_data.timestamp,
                trace_id=None,  # TODO: Get trace_id from context if available
                simulation_run_id=None,
                source=source,
                price_data=price_data,
                effective_price=price_data.price,
                price_validation=validation,
                allow_after_hours=allow_after_hours,
                trading_hours_policy=trading_hours_policy,
                position_qty=position.qty,
                position_cash=position.cash or 0.0,
                position_dividend_receivable=position.dividend_receivable or 0.0,
                anchor_price=position.anchor_price,
                anchor_reset_info=anchor_reset_info,
                trigger_config=trigger_config_dict,
                trigger_result=trigger_result,
                guardrail_config=guardrail_config_dict,
                guardrail_result=guardrail_result_dict,
                order_policy=order_policy_dict,
                order_proposal=order_proposal,
                action=action,
                action_reason=action_reason,
                order_id=order_id,
                trade_id=trade_id,
                execution_info=execution_info,
                position_qty_after=position_qty_after,
                position_cash_after=position_cash_after,
            )

            # Save to timeline (may fail if schema is incomplete, but we continue)
            try:
                self._logger.debug(
                    "Attempting to save timeline row for position %s.", position.id
                )
                record_id = self.evaluation_timeline_repo.save(timeline_row)
                self._logger.info(
                    "Timeline write result for position %s: success=True, record_id=%s, action=%s",
                    position.id, record_id, action
                )
                return record_id
            except Exception as timeline_error:
                # Don't fail evaluation if timeline write fails (e.g., missing columns)
                self._logger.warning(
                    "Timeline write result for position %s: success=False, error=%s",
                    position.id, timeline_error, exc_info=True
                )

            # Also write to PositionEvent (simplified immutable log)
            # This provides a compact audit trail for quick queries
            # Write PositionEvent even if timeline save failed (we have the data)
            try:
                from application.helpers.position_event_builder import (
                    build_position_event_from_timeline,
                )
                from app.di import container

                if hasattr(container, "position_event"):
                    event_data = build_position_event_from_timeline(timeline_row)
                    container.position_event.save(event_data)
            except Exception as event_error:
                # Don't fail if PositionEvent write fails
                self._logger.warning(
                    "Failed to write position event: %s", event_error, exc_info=True
                )

        except Exception as e:
            # Don't fail evaluation if timeline write fails
            self._logger.warning("Failed to write timeline row: %s", e, exc_info=True)
        return None

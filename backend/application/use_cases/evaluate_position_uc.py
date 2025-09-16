# =========================
# backend/application/use_cases/evaluate_position_uc.py
# =========================
from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
from domain.ports.positions_repo import PositionsRepo
from domain.ports.events_repo import EventsRepo
from domain.ports.market_data import MarketDataRepo
from domain.entities.event import Event
from infrastructure.time.clock import Clock
from uuid import uuid4


class EvaluatePositionUC:
    """Advanced volatility trading evaluation with order sizing and guardrails."""

    def __init__(
        self,
        positions: PositionsRepo,
        events: EventsRepo,
        market_data: MarketDataRepo,
        clock: Clock,
    ) -> None:
        self.positions = positions
        self.events = events
        self.market_data = market_data
        self.clock = clock

    def evaluate(self, position_id: str, current_price: float) -> Dict[str, Any]:
        """Evaluate position for volatility triggers with complete order sizing."""

        # Get position
        position = self.positions.get(position_id)
        if not position:
            raise KeyError("position_not_found")

        # Check if we have an anchor price
        if not position.anchor_price:
            return {
                "position_id": position_id,
                "current_price": current_price,
                "anchor_price": None,
                "trigger_detected": False,
                "reasoning": "No anchor price set - cannot evaluate triggers",
            }

        # Check triggers
        trigger_result = self._check_triggers(position, current_price)

        # Check for auto-rebalancing needs (if no trigger detected)
        rebalance_proposal = None
        if not trigger_result["triggered"]:
            rebalance_proposal = self._check_auto_rebalancing(position, current_price)
            if rebalance_proposal:
                trigger_result["triggered"] = True
                trigger_result["side"] = rebalance_proposal["side"]
                trigger_result["reasoning"] = rebalance_proposal["reasoning"]
                trigger_result["order_proposal"] = rebalance_proposal

        # If trigger detected, calculate order size and validate
        order_proposal = None
        if trigger_result["triggered"] and not rebalance_proposal:
            order_proposal = self._calculate_order_proposal(
                position, current_price, trigger_result["side"]
            )
            trigger_result["order_proposal"] = order_proposal

        # Log event
        self._log_evaluation_event(position, current_price, trigger_result)

        return {
            "position_id": position_id,
            "current_price": current_price,
            "anchor_price": position.anchor_price,
            "trigger_detected": trigger_result["triggered"],
            "trigger_type": trigger_result.get("side"),
            "order_proposal": order_proposal,
            "reasoning": trigger_result["reasoning"],
        }

    def evaluate_with_market_data(self, position_id: str) -> Dict[str, Any]:
        """Evaluate position using real-time market data with after-hours support."""

        # Get position
        position = self.positions.get(position_id)
        if not position:
            raise KeyError("position_not_found")

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
        price_data = self.market_data.get_reference_price(position.ticker)
        if not price_data:
            return {
                "position_id": position_id,
                "current_price": None,
                "anchor_price": position.anchor_price,
                "trigger_detected": False,
                "reasoning": "Unable to fetch market data",
                "market_data": None,
            }

        # Validate price data with after-hours setting
        validation = self.market_data.validate_price(
            price_data, allow_after_hours=position.order_policy.allow_after_hours
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

        # Check triggers with real market price
        trigger_result = self._check_triggers(position, price_data.price)

        # Check for auto-rebalancing needs (if no trigger detected)
        rebalance_proposal = None
        if not trigger_result["triggered"]:
            rebalance_proposal = self._check_auto_rebalancing(position, price_data.price)
            if rebalance_proposal:
                trigger_result["triggered"] = True
                trigger_result["side"] = rebalance_proposal["side"]
                trigger_result["reasoning"] = rebalance_proposal["reasoning"]
                trigger_result["order_proposal"] = rebalance_proposal

        # If trigger detected, calculate order size and validate
        order_proposal = None
        if trigger_result["triggered"] and not rebalance_proposal:
            order_proposal = self._calculate_order_proposal(
                position, price_data.price, trigger_result["side"]
            )
            trigger_result["order_proposal"] = order_proposal

        # Log event
        self._log_evaluation_event(position, price_data.price, trigger_result)

        return {
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

    def _check_triggers(self, position, current_price: float) -> Dict[str, Any]:
        """Check if current price triggers buy or sell."""
        anchor = position.anchor_price
        threshold = position.order_policy.trigger_threshold_pct

        # Buy trigger: P ≤ P_anchor × (1 − τ)
        buy_threshold = anchor * (1 - threshold)
        # Sell trigger: P ≥ P_anchor × (1 + τ)
        sell_threshold = anchor * (1 + threshold)

        if current_price <= buy_threshold:
            return {
                "triggered": True,
                "side": "BUY",
                "reasoning": f"Price ${current_price:.2f} ≤ buy threshold ${buy_threshold:.2f} (${anchor:.2f} × {1-threshold:.1%})",
            }
        elif current_price >= sell_threshold:
            return {
                "triggered": True,
                "side": "SELL",
                "reasoning": f"Price ${current_price:.2f} ≥ sell threshold ${sell_threshold:.2f} (${anchor:.2f} × {1+threshold:.1%})",
            }
        else:
            return {
                "triggered": False,
                "reasoning": f"Price ${current_price:.2f} within threshold range [${buy_threshold:.2f}, ${sell_threshold:.2f}]",
            }

    def _calculate_order_proposal(
        self, position, current_price: float, side: str
    ) -> Dict[str, Any]:
        """Calculate order size using the specification formula with guardrail trimming."""

        # Calculate portfolio values
        asset_value = position.qty * current_price
        total_value = asset_value + position.cash

        # Apply order sizing formula: ΔQ_raw = (P_anchor / P) × r × ((A + C) / P)
        anchor = position.anchor_price
        rebalance_ratio = position.order_policy.rebalance_ratio

        raw_qty = (anchor / current_price) * rebalance_ratio * (total_value / current_price)

        # Apply side (BUY = positive, SELL = negative)
        if side == "SELL":
            raw_qty = -raw_qty

        # Apply guardrail trimming
        trimmed_qty, trimming_reason = self._apply_guardrail_trimming(
            position, raw_qty, current_price, side
        )

        # Calculate order details
        notional = abs(trimmed_qty) * current_price
        commission = notional * position.order_policy.commission_rate

        # Validate order
        validation_result = self._validate_order(
            position, trimmed_qty, current_price, side, notional, commission
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
                position, trimmed_qty, current_price
            ),
        }

    def _apply_guardrail_trimming(
        self, position, raw_qty: float, current_price: float, side: str
    ) -> Tuple[float, str]:
        """Apply guardrail trimming to ensure Asset% ∈ [25%, 75%] post-trade."""

        # Calculate current allocation
        current_asset_value = position.qty * current_price

        # Calculate post-trade allocation without trimming
        post_qty = position.qty + raw_qty
        post_asset_value = post_qty * current_price
        post_cash = (
            position.cash
            - (raw_qty * current_price)
            - (abs(raw_qty) * current_price * position.order_policy.commission_rate)
        )
        post_total_value = post_asset_value + post_cash
        post_asset_pct = post_asset_value / post_total_value if post_total_value > 0 else 0

        # Check if trimming is needed
        min_alloc = position.guardrails.min_stock_alloc_pct
        max_alloc = position.guardrails.max_stock_alloc_pct

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
            reason = (
                f"Trimmed to reach maximum allocation {max_alloc:.1%} (was {post_asset_pct:.1%})"
            )
        else:
            # No trimming needed
            trimmed_qty = raw_qty
            reason = "No trimming needed - within guardrail bounds"

        return trimmed_qty, reason

    def _check_auto_rebalancing(self, position, current_price: float) -> Optional[Dict[str, Any]]:
        """Check if position needs auto-rebalancing due to drift outside guardrails."""

        # Calculate current allocation
        current_asset_value = position.qty * current_price
        current_total_value = current_asset_value + position.cash
        current_asset_pct = (
            current_asset_value / current_total_value if current_total_value > 0 else 0
        )

        min_alloc = position.guardrails.min_stock_alloc_pct
        max_alloc = position.guardrails.max_stock_alloc_pct

        # Check if we're outside guardrails
        if current_asset_pct < min_alloc:
            # Need to buy to reach minimum allocation
            target_asset_value = min_alloc * current_total_value
            target_qty = target_asset_value / current_price
            rebalance_qty = target_qty - position.qty

            if rebalance_qty > 0.001:  # Only rebalance if significant
                return {
                    "side": "BUY",
                    "reasoning": f"Auto-rebalance: Asset allocation {current_asset_pct:.1%} below minimum {min_alloc:.1%}",
                    "raw_qty": rebalance_qty,
                    "trimmed_qty": rebalance_qty,
                    "notional": rebalance_qty * current_price,
                    "commission": rebalance_qty
                    * current_price
                    * position.order_policy.commission_rate,
                    "trimming_reason": "Auto-rebalance to minimum allocation",
                    "validation": self._validate_order(
                        position,
                        rebalance_qty,
                        current_price,
                        "BUY",
                        rebalance_qty * current_price,
                        rebalance_qty * current_price * position.order_policy.commission_rate,
                    ),
                    "post_trade_asset_pct": min_alloc,
                }

        elif current_asset_pct > max_alloc:
            # Need to sell to reach maximum allocation
            target_asset_value = max_alloc * current_total_value
            target_qty = target_asset_value / current_price
            rebalance_qty = target_qty - position.qty

            if rebalance_qty < -0.001:  # Only rebalance if significant
                return {
                    "side": "SELL",
                    "reasoning": f"Auto-rebalance: Asset allocation {current_asset_pct:.1%} above maximum {max_alloc:.1%}",
                    "raw_qty": rebalance_qty,
                    "trimmed_qty": rebalance_qty,
                    "notional": abs(rebalance_qty) * current_price,
                    "commission": abs(rebalance_qty)
                    * current_price
                    * position.order_policy.commission_rate,
                    "trimming_reason": "Auto-rebalance to maximum allocation",
                    "validation": self._validate_order(
                        position,
                        rebalance_qty,
                        current_price,
                        "SELL",
                        abs(rebalance_qty) * current_price,
                        abs(rebalance_qty) * current_price * position.order_policy.commission_rate,
                    ),
                    "post_trade_asset_pct": max_alloc,
                }

        return None

    def _validate_order(
        self, position, qty: float, price: float, side: str, notional: float, commission: float
    ) -> Dict[str, Any]:
        """Validate order against business rules including market hours and duplicates."""

        validation_result = {"valid": True, "rejections": [], "warnings": []}

        # Check minimum notional
        if notional < position.order_policy.min_notional:
            validation_result["valid"] = False
            validation_result["rejections"].append(
                f"Notional ${notional:.2f} below minimum ${position.order_policy.min_notional:.2f}"
            )

        # Check sufficient cash for buy orders
        if side == "BUY":
            required_cash = (qty * price) + commission
            if required_cash > position.cash:
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

        # Check market hours (respect after-hours setting)
        if not self._is_market_hours():
            if not position.order_policy.allow_after_hours:
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

    def _is_market_hours(self) -> bool:
        """Check if current time is during market hours (simplified implementation)."""
        now = self.clock.now()

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
        post_qty = position.qty + qty
        post_asset_value = post_qty * price
        post_cash = (
            position.cash
            - (qty * price)
            - (abs(qty) * price * position.order_policy.commission_rate)
        )
        post_total_value = post_asset_value + post_cash

        return post_asset_value / post_total_value if post_total_value > 0 else 0

    def _log_evaluation_event(
        self, position, current_price: float, trigger_result: Dict[str, Any]
    ) -> None:
        """Log evaluation event with order proposal details."""

        # Prepare inputs
        inputs = {
            "current_price": current_price,
            "anchor_price": position.anchor_price,
            "threshold_pct": position.order_policy.trigger_threshold_pct,
            "current_qty": position.qty,
            "current_cash": position.cash,
            "current_asset_pct": (position.qty * current_price)
            / (position.qty * current_price + position.cash),
        }

        # Prepare outputs
        outputs = {
            "trigger_detected": trigger_result["triggered"],
            "trigger_type": trigger_result.get("side"),
            "reasoning": trigger_result["reasoning"],
        }

        # Add order proposal details if available
        if "order_proposal" in trigger_result and trigger_result["order_proposal"]:
            proposal = trigger_result["order_proposal"]
            inputs.update(
                {
                    "raw_qty": proposal["raw_qty"],
                    "rebalance_ratio": position.order_policy.rebalance_ratio,
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

        event = Event(
            id=f"evt_eval_{position.id}_{uuid4().hex[:8]}",
            position_id=position.id,
            type="threshold_crossed" if trigger_result["triggered"] else "evaluation_completed",
            inputs=inputs,
            outputs=outputs,
            message=trigger_result["reasoning"],
            ts=self.clock.now(),
        )
        self.events.append(event)

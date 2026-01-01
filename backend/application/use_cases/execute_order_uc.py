# backend/application/use_cases/execute_order_uc.py
from __future__ import annotations

from typing import Optional, Callable
from decimal import Decimal
from uuid import uuid4

from application.dto.orders import FillOrderRequest, FillOrderResponse
from domain.entities.event import Event
from domain.errors import GuardrailBreach
from domain.ports.events_repo import EventsRepo
from domain.ports.orders_repo import OrdersRepo
from domain.ports.positions_repo import PositionsRepo
from domain.ports.trades_repo import TradesRepo
from domain.services.guardrail_evaluator import GuardrailEvaluator
from domain.value_objects.configs import GuardrailConfig, OrderPolicyConfig
from infrastructure.time.clock import Clock
from infrastructure.adapters.converters import (
    guardrail_policy_to_guardrail_config,
    order_policy_to_order_policy_config,
    position_to_position_state,
)


class ExecuteOrderUC:
    """
    Applies an executed fill to a Position and emits events.

    Notes
    -----
    * Commission is taken from FillOrderRequest (default 0.0 if omitted).
    * "Below-min" order policy (min_qty / min_notional) is evaluated first.
      - action_below_min == "reject": order is marked rejected and an event is added.
      - action_below_min == "hold":   no position change; a 'skipped' event is added.
    * SELL guardrail: reject if requested fill exceeds current position qty.
    * After-fill guardrails: uses GuardrailEvaluator.validate_after_fill() to validate
      resulting cash/qty allocation. If invalid -> GuardrailBreach + event.
    * On success: updates position, marks order filled, appends 'order_filled' event.
    """

    def __init__(
        self,
        positions: PositionsRepo,
        orders: OrdersRepo,
        trades: TradesRepo,
        events: EventsRepo,
        clock: Optional[Clock] = None,
        guardrail_config_provider: Optional[Callable[[str, str, str], GuardrailConfig]] = None,
        order_policy_config_provider: Optional[Callable[[str, str, str], OrderPolicyConfig]] = None,
    ) -> None:
        self.positions = positions
        self.orders = orders
        self.trades = trades
        self.events = events
        self.clock = clock or Clock()
        # Config providers - if None, will fall back to extracting from Position entity (backward compat)
        self.guardrail_config_provider = guardrail_config_provider
        self.order_policy_config_provider = order_policy_config_provider

    def execute(self, order_id: str, request: FillOrderRequest) -> FillOrderResponse:
        order = self.orders.get(order_id)
        if not order:
            raise KeyError("order_not_found")

        # Check if order is already filled
        if order.status == "filled":
            return FillOrderResponse(order_id=order.id, status="filled", filled_qty=0.0)

        # Get position with tenant_id and portfolio_id from order
        pos = self.positions.get(
            tenant_id=order.tenant_id,
            portfolio_id=order.portfolio_id,
            position_id=order.position_id,
        )
        if not pos:
            raise KeyError("position_not_found")

        # Cash lives in position (cash lives in PositionCell per target state model)

        # Get order policy config for validation (utility methods still use pos.order_policy)
        if self.order_policy_config_provider:
            order_policy_config = self.order_policy_config_provider(
                order.tenant_id, order.portfolio_id, order.position_id
            )
        else:
            # Fallback: extract from Position entity (for backward compatibility)
            order_policy_config = (
                order_policy_to_order_policy_config(pos.order_policy) if pos.order_policy else None
            )

        # Normalize/round qty by order policy (utility methods - keep using pos.order_policy for now)
        policy = pos.order_policy
        q_req = abs(request.qty)
        q_req = policy.round_qty(q_req)
        q_req = policy.clamp_to_lot(q_req)
        commission = getattr(request, "commission", 0.0) or 0.0

        notional = q_req * request.price
        # Use config values for validation
        min_qty = float(order_policy_config.min_qty) if order_policy_config else policy.min_qty
        min_notional = (
            float(order_policy_config.min_notional) if order_policy_config else policy.min_notional
        )
        below_min = (min_qty > 0 and q_req < min_qty) or (
            min_notional > 0 and notional < min_notional
        )

        now = self.clock.now()
        uid = uuid4().hex[:8]  # unique suffix for event IDs

        # Get action_below_min from config
        action_below_min = (
            order_policy_config.action_below_min if order_policy_config else policy.action_below_min
        )

        # Below-min policy
        if below_min:
            if action_below_min == "reject":
                order.status = "rejected"
                self.orders.save(order)
                self.events.append(
                    Event(
                        id=f"evt_reject_{order.id}_{uid}",
                        position_id=order.position_id,
                        type="fill_rejected_below_min",
                        inputs={"qty": q_req, "price": request.price},
                        outputs={"order_id": order.id},
                        ts=now,
                        message="fill rejected: below minimum order policy",
                    )
                )
                return FillOrderResponse(order_id=order.id, status="rejected", filled_qty=0.0)
            else:
                # "hold"
                self.events.append(
                    Event(
                        id=f"evt_skip_{order.id}_{uid}",
                        position_id=order.position_id,
                        type="fill_skipped_below_min",
                        inputs={"qty": q_req, "price": request.price},
                        outputs={"order_id": order.id},
                        ts=now,
                        message="fill skipped: below minimum order policy",
                    )
                )
                return FillOrderResponse(order_id=order.id, status="skipped", filled_qty=0.0)

        # SELL guardrail: insufficient qty before applying any changes
        if order.side == "SELL" and q_req > pos.qty:
            self.events.append(
                Event(
                    id=f"evt_reject_{order.id}_{uid}",
                    position_id=order.position_id,
                    type="fill_rejected_insufficient_qty",
                    inputs={"qty": q_req, "price": request.price},
                    outputs={"order_id": order.id},
                    ts=now,
                    message="insufficient position qty",
                )
            )
            raise GuardrailBreach("insufficient_qty")

        # Validate after-fill guardrails using domain service
        # Get guardrail config from provider or fall back to extracting from Position (backward compat)
        if self.guardrail_config_provider:
            guardrail_config = self.guardrail_config_provider(
                order.tenant_id, order.portfolio_id, order.position_id
            )
        else:
            # Fallback: extract from Position entity (for backward compatibility)
            guardrail_config = guardrail_policy_to_guardrail_config(pos.guardrails)

        # Convert position to PositionState for domain service
        # Cash lives in position (cash lives in PositionCell)
        position_state = position_to_position_state(
            position=pos,
            cash=pos.cash,
        )

        # Use domain service for guardrail validation
        ok, why = GuardrailEvaluator.validate_after_fill(
            position_state=position_state,
            side=order.side,
            fill_qty=Decimal(str(q_req)),
            price=Decimal(str(request.price)),
            commission=Decimal(str(commission)),
            config=guardrail_config,
        )

        if not ok:
            self.events.append(
                Event(
                    id=f"evt_gr_{order.id}_{uid}",
                    position_id=order.position_id,
                    type="guardrail_breach",
                    inputs={
                        "side": order.side,
                        "qty": q_req,
                        "price": request.price,
                        "commission": commission,
                    },
                    outputs={"order_id": order.id, "reason": why},
                    ts=now,
                    message=f"guardrail breach: {why}",
                )
            )
            raise GuardrailBreach(why)

        # Calculate effective commission rate (actual rate applied)
        notional = q_req * request.price
        commission_rate_effective = commission / notional if notional > 0 else None

        # Apply the fill
        if order.side == "BUY":
            pos.qty += q_req
            # Update position cash (cash lives in PositionCell)
            pos.cash -= (q_req * request.price) + commission
        else:
            # SELL
            pos.qty -= q_req
            # Update position cash (cash lives in PositionCell)
            pos.cash += (q_req * request.price) - commission

        # Update commission aggregate (per spec)
        pos.total_commission_paid += commission

        # Create and persist trade record
        from domain.entities.trade import Trade

        trade = Trade(
            id=f"trd_{uuid4().hex[:8]}",
            tenant_id=order.tenant_id,
            portfolio_id=order.portfolio_id,
            order_id=order.id,
            position_id=order.position_id,
            side=order.side,  # OrderSide is a Literal type, so we can use the string directly
            qty=q_req,
            price=request.price,
            commission=commission,
            commission_rate_effective=commission_rate_effective,
            status="executed",
            executed_at=now,
        )
        self.trades.save(trade)

        # Calculate pre-trade state for logging (before anchor update)
        # Get cash from position (before the update we just made)
        pre_trade_cash = (
            pos.cash + (q_req * request.price) + commission
            if order.side == "BUY"
            else pos.cash - (q_req * request.price) + commission
        )
        pre_trade_qty = pos.qty - q_req if order.side == "BUY" else pos.qty + q_req
        pre_trade_market_value = pre_trade_qty * request.price
        pre_trade_total_value = pre_trade_cash + pre_trade_market_value
        pre_trade_asset_pct = (
            (pre_trade_market_value / pre_trade_total_value * 100)
            if pre_trade_total_value > 0
            else 0
        )

        # Update anchor price BEFORE saving position (so it gets persisted)
        old_anchor = pos.anchor_price
        pos.set_anchor_price(request.price)

        # Save position with updated anchor price
        self.positions.save(pos)

        order.status = "filled"
        self.orders.save(order)

        # Calculate post-trade state
        post_trade_market_value = pos.qty * request.price
        post_trade_total_value = pos.cash + post_trade_market_value
        post_trade_asset_pct = (
            (post_trade_market_value / post_trade_total_value * 100)
            if post_trade_total_value > 0
            else 0
        )

        # Calculate P&L if we have an anchor price
        pnl = 0.0
        pnl_pct = 0.0
        if old_anchor and old_anchor > 0:
            pnl = (request.price - old_anchor) * pos.qty
            pnl_pct = ((request.price - old_anchor) / old_anchor) * 100

        self.events.append(
            Event(
                id=f"evt_filled_{order.id}_{uid}",
                position_id=order.position_id,
                type="order_filled",
                inputs={
                    "qty": q_req,
                    "price": request.price,
                    "side": order.side,
                    "commission": commission,
                    "notional": q_req * request.price,
                    "pre_trade_cash": pre_trade_cash,
                    "pre_trade_qty": pre_trade_qty,
                    "pre_trade_market_value": pre_trade_market_value,
                    "pre_trade_total_value": pre_trade_total_value,
                    "pre_trade_asset_pct": pre_trade_asset_pct,
                },
                outputs={
                    "order_id": order.id,
                    "post_trade_cash": pos.cash,
                    "post_trade_qty": pos.qty,
                    "post_trade_market_value": post_trade_market_value,
                    "post_trade_total_value": post_trade_total_value,
                    "post_trade_asset_pct": post_trade_asset_pct,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                },
                ts=now,
                message=f"Order filled: {order.side} {q_req:.4f} @ ${request.price:.2f} (P&L: ${pnl:.2f}, {pnl_pct:.2f}%)",
            )
        )

        # Log anchor price update (if changed)
        if old_anchor != request.price:
            self.events.append(
                Event(
                    id=f"evt_anchor_{order.id}_{uid}",
                    position_id=order.position_id,
                    type="anchor_updated",
                    inputs={
                        "old_anchor": old_anchor,
                        "new_anchor": request.price,
                        "price_change": request.price - old_anchor if old_anchor else 0,
                        "price_change_pct": (
                            ((request.price - old_anchor) / old_anchor * 100)
                            if old_anchor and old_anchor > 0
                            else 0
                        ),
                    },
                    outputs={"anchor_price": request.price},
                    ts=now,
                    message=(
                        f"Anchor price updated from ${old_anchor:.2f} to ${request.price:.2f}"
                        if old_anchor is not None
                        else f"Anchor price set to ${request.price:.2f}"
                    ),
                )
            )

        return FillOrderResponse(
            order_id=order.id, status="filled", filled_qty=q_req, trade_id=trade.id
        )

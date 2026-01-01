# =========================
# backend/application/helpers/timeline_builder.py
# =========================
"""
Helper functions to build PositionEvaluationTimeline rows from evaluation results.

This module provides a single source of truth for converting evaluation data
into the canonical timeline format. No business logic is duplicated here -
it only transforms data structures.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4


def build_timeline_row_from_evaluation(
    *,
    mode: str,  # 'LIVE' or 'SIMULATION'
    tenant_id: str,
    portfolio_id: str,
    portfolio_name: Optional[str],
    position_id: str,
    symbol: str,
    timestamp: datetime,
    trace_id: Optional[str] = None,
    simulation_run_id: Optional[str] = None,
    source: Optional[str] = None,
    # Market data
    price_data: Optional[Any] = None,  # PriceData entity
    effective_price: Optional[float] = None,
    price_validation: Optional[Dict[str, Any]] = None,
    allow_after_hours: bool = False,
    trading_hours_policy: Optional[str] = None,
    # Position state before
    position_qty: float,
    position_cash: float,
    position_dividend_receivable: float = 0.0,
    # Strategy state
    anchor_price: Optional[float] = None,
    anchor_reset_info: Optional[Dict[str, Any]] = None,
    trigger_config: Optional[Dict[str, Any]] = None,
    trigger_result: Optional[Dict[str, Any]] = None,
    guardrail_config: Optional[Dict[str, Any]] = None,
    guardrail_result: Optional[Dict[str, Any]] = None,
    order_policy: Optional[Dict[str, Any]] = None,
    # Action decision
    order_proposal: Optional[Dict[str, Any]] = None,
    action: str = "HOLD",  # BUY, SELL, HOLD, SKIP
    action_reason: Optional[str] = None,
    # Execution result (if any)
    order_id: Optional[str] = None,
    trade_id: Optional[str] = None,
    execution_info: Optional[Dict[str, Any]] = None,
    # Position state after (if changed)
    position_qty_after: Optional[float] = None,
    position_cash_after: Optional[float] = None,
    # Portfolio impact
    portfolio_snapshot_before: Optional[Dict[str, Any]] = None,
    portfolio_snapshot_after: Optional[Dict[str, Any]] = None,
    # Dividend data (if applicable)
    dividend_info: Optional[Dict[str, Any]] = None,
    # Verbose fields (optional, for debug mode)
    evaluation_notes: Optional[str] = None,
    pricing_notes: Optional[str] = None,
    trigger_notes: Optional[str] = None,
    guardrail_notes: Optional[str] = None,
    action_notes: Optional[str] = None,
    warnings: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a PositionEvaluationTimeline row from evaluation data.

    This is the single source of truth for timeline row construction.
    All evaluation paths (live trading, simulation) use this function.

    Args:
        mode: 'LIVE' or 'SIMULATION'
        tenant_id: Tenant identifier
        portfolio_id: Portfolio identifier
        portfolio_name: Portfolio name (denormalized for readability)
        position_id: Position identifier
        symbol: Asset symbol
        timestamp: Evaluation timestamp (primary ordering key)
        trace_id: Optional trace ID linking related evaluations
        simulation_run_id: Optional simulation run ID (for SIMULATION mode)
        source: Source of evaluation ('worker', 'api/manual', 'simulation')

        # Market data
        price_data: PriceData entity with raw market data
        effective_price: Price actually used after policy validation
        price_validation: Validation result dict with 'valid', 'rejections', 'warnings'
        allow_after_hours: Whether after-hours trading is allowed
        trading_hours_policy: Portfolio trading hours policy

        # Position state before
        position_qty: Shares before evaluation
        position_cash: Cash before evaluation
        position_dividend_receivable: Dividend receivable before evaluation

        # Strategy state
        anchor_price: Current anchor price
        anchor_reset_info: Dict with 'occurred', 'old_value', 'reason' if anchor was reset
        trigger_config: Dict with trigger configuration
        trigger_result: Dict with trigger evaluation result
        guardrail_config: Dict with guardrail configuration
        guardrail_result: Dict with guardrail evaluation result
        order_policy: Dict with order policy configuration

        # Action decision
        order_proposal: Dict with order proposal details
        action: Action taken ('BUY', 'SELL', 'HOLD', 'SKIP')
        action_reason: Human-readable explanation of action

        # Execution result
        order_id: Order ID if order was created
        trade_id: Trade ID if trade was executed
        execution_info: Dict with execution details

        # Position state after
        position_qty_after: Shares after evaluation/execution
        position_cash_after: Cash after evaluation/execution

        # Portfolio impact
        portfolio_snapshot_before: Dict with portfolio totals before
        portfolio_snapshot_after: Dict with portfolio totals after

        # Dividend data
        dividend_info: Dict with dividend information

        # Verbose fields
        evaluation_notes: Free-form evaluation notes
        pricing_notes: Why this price was used
        trigger_notes: Math explanation for trigger
        guardrail_notes: Why guardrail allowed/blocked
        action_notes: Why this action was taken
        warnings: Warnings about liquidity, fallback, etc

    Returns:
        Dictionary ready to be saved to PositionEvaluationTimeline table
    """
    # Calculate derived values
    # Convert effective_price to float to avoid Decimal/float type mismatch
    effective_price_float = float(effective_price) if effective_price else 0.0
    stock_value_before = position_qty * effective_price_float
    total_value_before = position_cash + stock_value_before
    cash_pct = (position_cash / total_value_before * 100) if total_value_before > 0 else 0.0
    stock_pct = (stock_value_before / total_value_before * 100) if total_value_before > 0 else 0.0

    # Calculate anchor deltas
    pct_change_from_anchor = None
    if anchor_price and effective_price:
        # Convert anchor_price to float for comparison
        anchor_price_float = float(anchor_price)
        pct_change_from_anchor = (
            (effective_price_float - anchor_price_float) / anchor_price_float
        ) * 100

    # Determine market session
    market_session = None
    if price_data:
        if price_data.is_market_hours:
            market_session = "REGULAR"
        else:
            market_session = "EXTENDED"

    # Extract trigger direction
    trigger_direction = None
    if trigger_result:
        if trigger_result.get("triggered"):
            side = trigger_result.get("side", "")
            if side == "BUY":
                trigger_direction = "UP"
            elif side == "SELL":
                trigger_direction = "DOWN"
        else:
            trigger_direction = "NONE"

    # Build action fields
    trade_intent_qty = None
    trade_intent_value = None
    trade_intent_cash_delta = None

    if order_proposal:
        trade_intent_qty = order_proposal.get("trimmed_qty") or order_proposal.get("raw_qty")
        trade_intent_value = order_proposal.get("notional")
        if trade_intent_qty and effective_price:
            # Cash delta: negative for BUY (spend cash), positive for SELL (receive cash)
            # Convert effective_price to float to avoid Decimal/float type mismatch
            effective_price_float = float(effective_price)
            side = order_proposal.get("side", "")
            commission = order_proposal.get("commission", 0.0)
            if side == "BUY":
                trade_intent_cash_delta = -(
                    abs(trade_intent_qty) * effective_price_float + commission
                )
            elif side == "SELL":
                trade_intent_cash_delta = abs(trade_intent_qty) * effective_price_float - commission

    # Calculate position state after
    stock_value_after = None
    total_value_after = None
    stock_pct_after = None

    if position_qty_after is not None and effective_price:
        # Convert effective_price to float to avoid Decimal/float type mismatch
        effective_price_float = float(effective_price)
        stock_value_after = position_qty_after * effective_price_float
        total_value_after = (position_cash_after or position_cash) + stock_value_after
        stock_pct_after = (
            (stock_value_after / total_value_after * 100) if total_value_after > 0 else 0.0
        )

    # Calculate portfolio impact
    position_weight_pct_before = None
    position_weight_pct_after = None

    if portfolio_snapshot_before:
        portfolio_total = portfolio_snapshot_before.get("total_value", 0.0)
        if portfolio_total > 0:
            position_weight_pct_before = (total_value_before / portfolio_total) * 100

    if portfolio_snapshot_after:
        portfolio_total_after = portfolio_snapshot_after.get("total_value", 0.0)
        if portfolio_total_after > 0 and total_value_after:
            position_weight_pct_after = (total_value_after / portfolio_total_after) * 100

    # Determine evaluation_type based on context
    evaluation_type = "DAILY_CHECK"  # Default
    if dividend_info and dividend_info.get("applied", False):
        evaluation_type = "DIVIDEND"
    elif order_id or trade_id:
        if trade_id:
            evaluation_type = "EXECUTION"
        else:
            evaluation_type = "TRADE_INTENT"
    elif trigger_result and trigger_result.get("triggered"):
        evaluation_type = "PRICE_UPDATE"  # Price update that triggered evaluation
    elif price_data and price_data.timestamp:
        # If we have fresh price data, it's a price update
        evaluation_type = "PRICE_UPDATE"

    # Build the row
    row = {
        "id": f"eval_{uuid4().hex[:16]}",
        "tenant_id": tenant_id,
        "portfolio_id": portfolio_id,
        "portfolio_name": portfolio_name,
        "position_id": position_id,
        "symbol": symbol,
        "exchange": None,  # TODO: Extract from market data if available
        "timestamp": timestamp,
        "market_session": market_session,
        "evaluation_type": evaluation_type,
        "evaluation_seq": None,  # Will be calculated by repository
        "trace_id": trace_id,
        "mode": mode,
        "simulation_run_id": simulation_run_id,
        "source": source,
        # Market data - OHLCV
        "open_price": price_data.open if price_data else None,
        "high_price": price_data.high if price_data else None,
        "low_price": price_data.low if price_data else None,
        "close_price": price_data.close if price_data else None,
        "volume": float(price_data.volume) if price_data and price_data.volume else None,
        # Market data - Quote details
        "last_trade_price": price_data.last_trade_price if price_data else None,
        "best_bid": price_data.bid if price_data else None,
        "best_ask": price_data.ask if price_data else None,
        "official_close_price": price_data.close if price_data else None,  # Previous close
        "effective_price": effective_price,
        "price_policy_requested": price_data.source.value if price_data else None,
        "price_policy_effective": (
            price_data.source.value if price_data else None
        ),  # TODO: Track fallbacks
        "price_fallback_reason": None,  # TODO: Track if fallback occurred
        "data_provider": "yfinance",  # TODO: Extract from market data adapter
        # Market hours validation
        "is_market_hours": price_data.is_market_hours if price_data else True,
        "allow_after_hours": allow_after_hours,
        "trading_hours_policy": trading_hours_policy,
        "price_validation_valid": price_validation.get("valid") if price_validation else None,
        "price_validation_rejections": (
            price_validation.get("rejections") if price_validation else None
        ),
        "price_validation_warnings": price_validation.get("warnings") if price_validation else None,
        "is_fresh": price_data.is_fresh if price_data else True,
        "is_inline": price_data.is_inline if price_data else True,
        # Position state before
        "position_qty_before": position_qty,
        "position_cash_before": position_cash,
        "position_stock_value_before": stock_value_before,
        "position_total_value_before": total_value_before,
        "cash_pct": cash_pct,
        "stock_pct": stock_pct,
        "position_dividend_receivable_before": position_dividend_receivable,
        # Dividend data
        "dividend_declared": dividend_info.get("declared", False) if dividend_info else False,
        "dividend_ex_date": dividend_info.get("ex_date") if dividend_info else None,
        "dividend_pay_date": dividend_info.get("pay_date") if dividend_info else None,
        "dividend_rate": dividend_info.get("rate") if dividend_info else None,
        "dividend_gross_value": dividend_info.get("gross_value") if dividend_info else None,
        "dividend_tax": dividend_info.get("tax") if dividend_info else None,
        "dividend_net_value": dividend_info.get("net_value") if dividend_info else None,
        "dividend_applied": dividend_info.get("applied", False) if dividend_info else False,
        # Strategy state - Anchor
        "anchor_price": anchor_price,
        "pct_change_from_anchor": pct_change_from_anchor,
        "pct_change_from_prev": None,  # TODO: Calculate from previous row
        "anchor_updated": anchor_reset_info.get("occurred", False) if anchor_reset_info else False,
        "anchor_reset_old_value": anchor_reset_info.get("old_value") if anchor_reset_info else None,
        "anchor_reset_reason": anchor_reset_info.get("reason") if anchor_reset_info else None,
        # Strategy state - Triggers
        "trigger_up_threshold": trigger_config.get("up_threshold_pct") if trigger_config else None,
        "trigger_down_threshold": (
            trigger_config.get("down_threshold_pct") if trigger_config else None
        ),
        "trigger_direction": trigger_direction,
        "trigger_fired": trigger_result.get("triggered", False) if trigger_result else False,
        "trigger_reason": trigger_result.get("reasoning") if trigger_result else None,
        # Strategy state - Guardrails
        "guardrail_min_stock_pct": (
            guardrail_config.get("min_stock_pct") if guardrail_config else None
        ),
        "guardrail_max_stock_pct": (
            guardrail_config.get("max_stock_pct") if guardrail_config else None
        ),
        "guardrail_max_trade_pct": (
            guardrail_config.get("max_trade_pct_of_position") if guardrail_config else None
        ),
        "guardrail_max_orders_per_day": (
            guardrail_config.get("max_orders_per_day") if guardrail_config else None
        ),
        "guardrail_allowed": guardrail_result.get("allowed") if guardrail_result else None,
        "guardrail_block_reason": (
            guardrail_result.get("reason")
            if guardrail_result and not guardrail_result.get("allowed")
            else None
        ),
        # Order policy (for reference)
        "order_policy_rebalance_ratio": (
            order_policy.get("rebalance_ratio") if order_policy else None
        ),
        "order_policy_commission_rate": (
            order_policy.get("commission_rate") if order_policy else None
        ),
        "order_policy_min_qty": order_policy.get("min_qty") if order_policy else None,
        "order_policy_min_notional": order_policy.get("min_notional") if order_policy else None,
        # Action decision
        "action": action,
        "action_reason": action_reason,
        "trade_intent_qty": trade_intent_qty,
        "trade_intent_value": trade_intent_value,
        "trade_intent_cash_delta": trade_intent_cash_delta,
        # Legacy action fields (for backward compatibility)
        "action_taken": action,  # Map action to action_taken
        "action_side": order_proposal.get("side") if order_proposal else None,
        "action_qty_raw": order_proposal.get("raw_qty") if order_proposal else None,
        "action_qty_trimmed": order_proposal.get("trimmed_qty") if order_proposal else None,
        "action_notional": order_proposal.get("notional") if order_proposal else None,
        "action_commission_estimated": order_proposal.get("commission") if order_proposal else None,
        "action_trimming_reason": order_proposal.get("trimming_reason") if order_proposal else None,
        "decision_allowed": guardrail_result.get("allowed") if guardrail_result else None,
        "decision_rejections": (
            order_proposal.get("validation", {}).get("rejections") if order_proposal else None
        ),
        "decision_warnings": (
            order_proposal.get("validation", {}).get("warnings") if order_proposal else None
        ),
        "decision_explanation": action_reason,
        # Post-trade projection
        "post_trade_stock_pct": (
            order_proposal.get("post_trade_asset_pct") if order_proposal else None
        ),
        "post_trade_stock_value": None,  # TODO: Calculate from post_trade_asset_pct
        "post_trade_cash": None,  # TODO: Calculate from trade_intent_cash_delta
        "post_trade_total_value": None,  # TODO: Calculate
        # Execution result
        "order_id": order_id,
        "trade_id": trade_id,
        "execution_price": execution_info.get("price") if execution_info else None,
        "execution_qty": execution_info.get("qty") if execution_info else None,
        "execution_commission": execution_info.get("commission") if execution_info else None,
        "execution_commission_rate_effective": (
            execution_info.get("commission_rate") if execution_info else None
        ),
        "execution_timestamp": execution_info.get("timestamp") if execution_info else None,
        "execution_status": execution_info.get("status") if execution_info else None,
        "commission_rate": execution_info.get("commission_rate") if execution_info else None,
        "commission_value": execution_info.get("commission") if execution_info else None,
        # Position state after
        "position_qty_after": position_qty_after,
        "position_cash_after": position_cash_after,
        "position_stock_value_after": stock_value_after,
        "position_total_value_after": total_value_after,
        "position_stock_pct_after": stock_pct_after,
        "new_anchor_price": anchor_reset_info.get("new_value") if anchor_reset_info else None,
        # Portfolio impact
        "portfolio_total_value_before": (
            portfolio_snapshot_before.get("total_value") if portfolio_snapshot_before else None
        ),
        "portfolio_total_value_after": (
            portfolio_snapshot_after.get("total_value") if portfolio_snapshot_after else None
        ),
        "portfolio_cash_before": (
            portfolio_snapshot_before.get("cash") if portfolio_snapshot_before else None
        ),
        "portfolio_cash_after": (
            portfolio_snapshot_after.get("cash") if portfolio_snapshot_after else None
        ),
        "portfolio_stock_value_before": (
            portfolio_snapshot_before.get("stock_value") if portfolio_snapshot_before else None
        ),
        "portfolio_stock_value_after": (
            portfolio_snapshot_after.get("stock_value") if portfolio_snapshot_after else None
        ),
        "position_weight_pct_before": position_weight_pct_before,
        "position_weight_pct_after": position_weight_pct_after,
        # Verbose explanation fields
        "evaluation_notes": evaluation_notes,
        "pricing_notes": pricing_notes,
        "trigger_notes": trigger_notes,
        "guardrail_notes": guardrail_notes,
        "action_notes": action_notes,
        "warnings": warnings,
        # Legacy verbose fields
        "evaluation_summary": action_reason,  # Use action_reason as summary
        "evaluation_details": None,  # Can be populated with full evaluation dict if needed
        "market_data_details": None,  # Can be populated with full price_data dict if needed
        "strategy_state_details": None,  # Can be populated with full config dicts if needed
        "execution_details": execution_info,  # Full execution info
    }

    return row

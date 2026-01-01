# =========================
# backend/infrastructure/adapters/converters.py
# =========================
"""Type conversion utilities between entities and value objects."""

from decimal import Decimal
from typing import Optional

from domain.entities.position import Position
from domain.entities.market_data import PriceData
from domain.value_objects.position_state import PositionState
from domain.value_objects.market import MarketQuote
from domain.value_objects.configs import TriggerConfig, GuardrailConfig, OrderPolicyConfig
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.guardrails import GuardrailPolicy


def position_to_position_state(position: Position, cash: Optional[float] = None) -> PositionState:
    """Convert Position entity to PositionState value object.

    Args:
        position: Position entity (no longer contains cash)
        cash: Optional cash override (defaults to position.cash)
    """
    if cash is None:
        # Default to 0 if cash not provided (shouldn't happen in production)
        cash = 0.0

    return PositionState(
        ticker=position.asset_symbol,  # Use asset_symbol instead of ticker property
        qty=Decimal(str(position.qty)),
        cash=Decimal(str(cash)),
        dividend_receivable=Decimal(str(position.dividend_receivable)),
        anchor_price=(
            Decimal(str(position.anchor_price)) if position.anchor_price is not None else None
        ),
    )


def price_data_to_market_quote(price_data: PriceData) -> MarketQuote:
    """Convert PriceData entity to MarketQuote value object."""
    return MarketQuote(
        ticker=price_data.ticker,
        price=Decimal(str(price_data.price)),
        timestamp=price_data.timestamp,
        currency="USD",  # Default, could be extracted from price_data if available
    )


def order_policy_to_trigger_config(order_policy: OrderPolicy) -> TriggerConfig:
    """Convert OrderPolicy to TriggerConfig."""
    threshold_pct = Decimal(str(order_policy.trigger_threshold_pct * 100))  # Convert to percentage
    return TriggerConfig(
        up_threshold_pct=threshold_pct,
        down_threshold_pct=threshold_pct,
    )


def guardrail_policy_to_guardrail_config(guardrail_policy: GuardrailPolicy) -> GuardrailConfig:
    """Convert GuardrailPolicy to GuardrailConfig."""
    return GuardrailConfig(
        min_stock_pct=Decimal(str(guardrail_policy.min_stock_alloc_pct)),
        max_stock_pct=Decimal(str(guardrail_policy.max_stock_alloc_pct)),
        max_trade_pct_of_position=(
            Decimal(str(guardrail_policy.max_sell_pct_per_trade))
            if guardrail_policy.max_sell_pct_per_trade
            else None
        ),
        max_daily_notional=None,  # Not in GuardrailPolicy, would need to be added
        max_orders_per_day=guardrail_policy.max_orders_per_day,
    )


def position_state_to_position(
    state: PositionState,
    position_id: str,
    tenant_id: str = "default",
    portfolio_id: str = "default",
) -> Position:
    """Convert PositionState value object to Position entity.

    Note: This creates a new Position with default policies.
    Use this carefully as it loses some entity state.
    Cash is stored in Position.cash.
    """
    from domain.value_objects.order_policy import OrderPolicy
    from domain.value_objects.guardrails import GuardrailPolicy

    return Position(
        id=position_id,
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        asset_symbol=state.ticker,  # Use asset_symbol instead of ticker
        qty=float(state.qty),
        # cash is stored in Position.cash
        anchor_price=float(state.anchor_price) if state.anchor_price is not None else None,
        dividend_receivable=float(state.dividend_receivable),
        order_policy=OrderPolicy(),  # Default
        guardrails=GuardrailPolicy(),  # Default
    )


def market_quote_to_price_data(quote: MarketQuote) -> PriceData:
    """Convert MarketQuote value object to PriceData entity.

    Note: This creates a minimal PriceData with defaults.
    """
    from domain.entities.market_data import PriceSource

    return PriceData(
        ticker=quote.ticker,
        price=float(quote.price),
        source=PriceSource.LAST_TRADE,
        timestamp=quote.timestamp,
    )


def order_policy_to_order_policy_config(order_policy: OrderPolicy) -> OrderPolicyConfig:
    """Convert OrderPolicy to OrderPolicyConfig."""
    from decimal import Decimal

    return OrderPolicyConfig(
        min_qty=Decimal(str(order_policy.min_qty)),
        min_notional=Decimal(str(order_policy.min_notional)),
        lot_size=Decimal(str(order_policy.lot_size)),
        qty_step=Decimal(str(order_policy.qty_step)),
        action_below_min=order_policy.action_below_min,
        rebalance_ratio=Decimal(str(order_policy.rebalance_ratio)),
        order_sizing_strategy=order_policy.order_sizing_strategy,
        allow_after_hours=order_policy.allow_after_hours,
    )


def get_trigger_threshold_from_position(position: Position) -> float:
    """
    Helper to extract trigger threshold from Position entity.

    This is a migration helper - eventually Position won't have order_policy.
    For now, this provides a consistent way to get the threshold.
    """
    return position.order_policy.trigger_threshold_pct

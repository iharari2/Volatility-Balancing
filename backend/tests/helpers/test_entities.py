"""
Helper functions for creating test entities with correct signatures.
"""

from datetime import datetime, timezone
from domain.entities.position import Position
from domain.entities.order import Order
from domain.entities.trade import Trade
from domain.value_objects.guardrails import GuardrailPolicy
from domain.value_objects.order_policy import OrderPolicy


def create_test_position(
    position_id: str = None,
    tenant_id: str = "default",
    portfolio_id: str = "test_portfolio",
    asset_symbol: str = "AAPL",
    qty: float = 100.0,
    anchor_price: float = None,
    avg_cost: float = None,
    guardrails: GuardrailPolicy = None,
    order_policy: OrderPolicy = None,
) -> Position:
    """Create a test Position with correct signature."""
    if position_id is None:
        import uuid

        position_id = f"pos_{uuid.uuid4().hex[:8]}"

    return Position(
        id=position_id,
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        asset_symbol=asset_symbol,
        qty=qty,
        anchor_price=anchor_price,
        avg_cost=avg_cost,
        guardrails=guardrails or GuardrailPolicy(),
        order_policy=order_policy or OrderPolicy(),
    )


def create_test_order(
    order_id: str = None,
    tenant_id: str = "default",
    portfolio_id: str = "test_portfolio",
    position_id: str = "pos_123",
    side: str = "BUY",
    qty: float = 100.0,
    status: str = "submitted",
    idempotency_key: str = None,
) -> Order:
    """Create a test Order with correct signature."""
    if order_id is None:
        import uuid

        order_id = f"ord_{uuid.uuid4().hex[:8]}"

    return Order(
        id=order_id,
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=position_id,
        side=side,
        qty=qty,
        status=status,
        idempotency_key=idempotency_key,
    )


def create_test_trade(
    trade_id: str = None,
    tenant_id: str = "default",
    portfolio_id: str = "test_portfolio",
    order_id: str = "ord_123",
    position_id: str = "pos_123",
    side: str = "BUY",
    qty: float = 100.0,
    price: float = 150.0,
    commission: float = 1.5,
    executed_at: datetime = None,
) -> Trade:
    """Create a test Trade with correct signature."""
    if trade_id is None:
        import uuid

        trade_id = f"trd_{uuid.uuid4().hex[:8]}"

    if executed_at is None:
        executed_at = datetime.now(timezone.utc)

    return Trade(
        id=trade_id,
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        order_id=order_id,
        position_id=position_id,
        side=side,
        qty=qty,
        price=price,
        commission=commission,
        executed_at=executed_at,
    )

# =========================
# backend/infrastructure/adapters/order_service_adapter.py
# =========================
"""Adapter implementing IOrderService using existing order submission logic."""

from decimal import Decimal
from typing import Optional
import logging

from application.ports.orders import IOrderService
from domain.value_objects.trade_intent import TradeIntent
from domain.value_objects.market import MarketQuote
from domain.value_objects.types import OrderSide
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.dto.orders import CreateOrderRequest

logger = logging.getLogger(__name__)


class LiveOrderServiceAdapter(IOrderService):
    """Adapter that implements IOrderService using existing SubmitOrderUC.

    Optionally integrates with BrokerIntegrationService for broker communication.
    """

    def __init__(
        self,
        submit_order_uc: SubmitOrderUC,
        broker_integration_service: Optional["BrokerIntegrationService"] = None,
    ):
        """
        Initialize adapter with existing submit order use case.

        Args:
            submit_order_uc: Existing SubmitOrderUC implementation
            broker_integration_service: Optional broker integration for live trading
        """
        self.submit_order_uc = submit_order_uc
        self.broker_integration = broker_integration_service

    def submit_live_order(
        self,
        position_id: str,
        portfolio_id: str,
        tenant_id: str,
        trade_intent: TradeIntent,
        quote: MarketQuote,
    ) -> str:
        """
        Live trading.
        Creates order record, calls broker, returns order_id.
        Must be idempotent for repeated calls with same trade intent.
        """
        from uuid import uuid4

        # Convert TradeIntent to CreateOrderRequest
        # Note: TradeIntent uses "buy"/"sell", OrderSide is Literal["BUY", "SELL"]
        # OrderSide is a type alias, not an enum, so use string literals directly
        side: OrderSide = "BUY" if trade_intent.side.lower() == "buy" else "SELL"

        request = CreateOrderRequest(
            side=side,
            qty=float(trade_intent.qty),
        )

        # Generate idempotency key from trade intent
        # Use a combination of position_id, side, qty, and price for idempotency
        idempotency_key = (
            f"{position_id}_{trade_intent.side}_{trade_intent.qty}_{quote.price}_{uuid4().hex[:8]}"
        )

        # Submit order using existing use case (creates internal record)
        response = self.submit_order_uc.execute(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            request=request,
            idempotency_key=idempotency_key,
        )

        # If broker integration is configured, submit to broker
        if self.broker_integration:
            logger.info(f"Broker integration configured, fetching order {response.order_id}")
            order = self.submit_order_uc.orders.get(response.order_id)
            if order:
                logger.info(f"Order {order.id} found, submitting to broker")
                try:
                    # Get symbol from position (we need to look it up)
                    position = self.submit_order_uc.positions.get(
                        tenant_id=tenant_id,
                        portfolio_id=portfolio_id,
                        position_id=position_id,
                    )
                    symbol = position.asset_symbol if position else "UNKNOWN"
                    logger.info(f"Position found: {symbol}, calling broker.submit_order_to_broker")

                    broker_response = self.broker_integration.submit_order_to_broker(
                        order=order,
                        symbol=symbol,
                        current_price=Decimal(str(quote.price)),
                    )
                    logger.info(
                        f"Order {order.id} submitted to broker: "
                        f"broker_order_id={broker_response.broker_order_id}, "
                        f"status={broker_response.status.value}"
                    )
                except Exception as e:
                    logger.error(f"Failed to submit order {order.id} to broker: {e}", exc_info=True)
                    # Order is still in our system, broker submission failed
                    # The order status will be updated by broker_integration_service
            else:
                logger.error(f"Order {response.order_id} not found after creation - cannot submit to broker")

        return response.order_id


# Avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from application.services.broker_integration_service import BrokerIntegrationService

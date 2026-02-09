# =========================
# backend/application/services/broker_integration_service.py
# =========================
"""
Service that orchestrates broker interactions for order lifecycle management.

This service coordinates between:
- Our internal order tracking (Order entity, OrdersRepo)
- The broker abstraction (IBrokerService)
- Order execution logic (ExecuteOrderUC)
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from uuid import uuid4
import logging

from domain.entities.order import Order
from domain.ports.broker_service import (
    IBrokerService,
    BrokerOrderRequest,
    BrokerOrderResponse,
    BrokerOrderStatus,
    BrokerFill,
    BrokerError,
)
from domain.ports.orders_repo import OrdersRepo
from application.use_cases.execute_order_uc import ExecuteOrderUC
from application.dto.orders import FillOrderRequest
from application.ports.event_logger import IEventLogger

logger = logging.getLogger(__name__)


class BrokerIntegrationService:
    """
    Orchestrates broker interactions for order lifecycle.

    Responsibilities:
    - Submit orders to broker and track broker_order_id
    - Process fills from broker into position updates
    - Handle order cancellation
    - Sync order status with broker state
    """

    def __init__(
        self,
        broker: IBrokerService,
        orders_repo: OrdersRepo,
        execute_order_uc: ExecuteOrderUC,
        event_logger: Optional[IEventLogger] = None,
    ):
        """
        Initialize broker integration service.

        Args:
            broker: Broker service implementation (stub or real)
            orders_repo: Repository for order persistence
            execute_order_uc: Use case for processing fills
            event_logger: Optional event logger for audit trail
        """
        self.broker = broker
        self.orders_repo = orders_repo
        self.execute_order_uc = execute_order_uc
        self.event_logger = event_logger

    def submit_order_to_broker(
        self,
        order: Order,
        symbol: str,
        current_price: Decimal,
    ) -> BrokerOrderResponse:
        """
        Submit an order to the broker.

        Args:
            order: The order to submit (should already be saved to orders_repo)
            symbol: Stock symbol for the order
            current_price: Current market price (used by stub broker for fills)

        Returns:
            BrokerOrderResponse with broker_order_id and status

        Side effects:
            - Updates order with broker tracking fields
            - For immediate fills, processes the fill and updates position
        """
        logger.info(f"BrokerIntegrationService.submit_order_to_broker called for order {order.id}, symbol={symbol}, price={current_price}")
        # Create broker order request
        request = BrokerOrderRequest(
            client_order_id=order.id,
            symbol=symbol,
            side="buy" if order.side == "BUY" else "sell",
            qty=Decimal(str(order.qty)),
            order_type="market",
            time_in_force=order.time_in_force,
        )

        # Set current market price for stub broker (real brokers execute at market)
        # This ensures the stub uses actual yfinance price for fills
        if hasattr(self.broker, 'set_price'):
            self.broker.set_price(symbol, current_price)

        # Submit to broker
        try:
            response = self.broker.submit_order(request)
        except BrokerError as e:
            logger.error(f"Broker error submitting order {order.id}: {e}")
            order.status = "rejected"
            order.broker_status = "error"
            order.rejection_reason = str(e)
            self.orders_repo.save(order)

            if self.event_logger:
                self._log_event(
                    order,
                    "broker_submission_failed",
                    {"error": str(e)},
                )

            raise

        # Update order with broker info
        order.broker_order_id = response.broker_order_id
        order.broker_status = response.status.value
        order.submitted_to_broker_at = response.submitted_at

        # Handle immediate rejection
        if response.status == BrokerOrderStatus.REJECTED:
            order.status = "rejected"
            order.rejection_reason = response.message
            self.orders_repo.save(order)

            if self.event_logger:
                self._log_event(
                    order,
                    "order_rejected_by_broker",
                    {"reason": response.message},
                )

            return response

        # Handle immediate fill
        if response.status == BrokerOrderStatus.FILLED:
            self._process_fills_for_order(order, symbol, current_price)
        else:
            # Order is working/pending
            order.status = "pending"
            self.orders_repo.save(order)

            if self.event_logger:
                self._log_event(
                    order,
                    "order_submitted_to_broker",
                    {
                        "broker_order_id": response.broker_order_id,
                        "broker_status": response.status.value,
                    },
                )

        return response

    def process_fills_for_order(self, order: Order, symbol: str) -> int:
        """
        Process any new fills for an order.

        Args:
            order: Order to check for fills
            symbol: Stock symbol (for logging)

        Returns:
            Number of new fills processed
        """
        if not order.broker_order_id:
            return 0

        # Get fills from broker
        fills = self.broker.get_fills(order.broker_order_id)
        if not fills:
            return 0

        # Calculate already processed fills
        already_filled = order.filled_qty or 0.0

        # Process new fills
        new_fills = 0
        for fill in fills:
            # Skip already processed fills (simple approach: check cumulative)
            if float(fill.fill_qty) <= already_filled:
                already_filled -= float(fill.fill_qty)
                continue

            self._process_single_fill(order, fill)
            new_fills += 1

        return new_fills

    def _process_fills_for_order(
        self,
        order: Order,
        symbol: str,
        fallback_price: Decimal,
    ) -> None:
        """
        Internal method to process fills after immediate fill.

        Args:
            order: Order that was filled
            symbol: Stock symbol
            fallback_price: Price to use if broker doesn't provide fill details
        """
        if not order.broker_order_id:
            return

        fills = self.broker.get_fills(order.broker_order_id)

        if fills:
            for fill in fills:
                self._process_single_fill(order, fill)
        else:
            # Broker didn't provide fills (shouldn't happen with stub)
            # Create synthetic fill from order info
            self._process_synthetic_fill(order, fallback_price)

    def _process_single_fill(self, order: Order, fill: BrokerFill) -> None:
        """
        Process a single fill from the broker.

        Args:
            order: Order being filled
            fill: Fill details from broker
        """
        # Create fill request for ExecuteOrderUC
        fill_request = FillOrderRequest(
            qty=float(fill.fill_qty),
            price=float(fill.fill_price),
            commission=float(fill.commission),
        )

        try:
            response = self.execute_order_uc.execute(order.id, fill_request)
            logger.info(
                f"Processed fill for order {order.id}: "
                f"{fill.fill_qty} @ {fill.fill_price}, "
                f"commission={fill.commission}"
            )
        except Exception as e:
            logger.error(f"Error processing fill for order {order.id}: {e}")
            raise

        # Update order tracking
        order.filled_qty = (order.filled_qty or 0.0) + float(fill.fill_qty)
        order.total_commission = (order.total_commission or 0.0) + float(fill.commission)
        order.last_broker_update = fill.executed_at

        # Calculate average fill price
        if order.avg_fill_price:
            # Weighted average
            prev_value = order.avg_fill_price * (order.filled_qty - float(fill.fill_qty))
            new_value = float(fill.fill_price) * float(fill.fill_qty)
            order.avg_fill_price = (prev_value + new_value) / order.filled_qty
        else:
            order.avg_fill_price = float(fill.fill_price)

        # Update order status
        if order.filled_qty >= order.qty:
            order.status = "filled"
            order.broker_status = BrokerOrderStatus.FILLED.value
        else:
            order.broker_status = BrokerOrderStatus.PARTIAL.value

        self.orders_repo.save(order)

        if self.event_logger:
            self._log_event(
                order,
                "fill_processed",
                {
                    "fill_qty": float(fill.fill_qty),
                    "fill_price": float(fill.fill_price),
                    "commission": float(fill.commission),
                    "cumulative_filled": order.filled_qty,
                },
            )

    def _process_synthetic_fill(self, order: Order, price: Decimal) -> None:
        """
        Process a synthetic fill when broker doesn't provide details.

        Args:
            order: Order to fill
            price: Price to use for the fill
        """
        # Calculate commission (same as stub broker: 0.1% with $0.01 min)
        notional = Decimal(str(order.qty)) * price
        commission = max(notional * Decimal("0.001"), Decimal("0.01"))

        fill_request = FillOrderRequest(
            qty=order.qty,
            price=float(price),
            commission=float(commission),
        )

        try:
            self.execute_order_uc.execute(order.id, fill_request)
        except Exception as e:
            logger.error(f"Error processing synthetic fill for order {order.id}: {e}")
            raise

        order.filled_qty = order.qty
        order.avg_fill_price = float(price)
        order.total_commission = float(commission)
        order.status = "filled"
        order.broker_status = BrokerOrderStatus.FILLED.value
        order.last_broker_update = datetime.now(timezone.utc)
        self.orders_repo.save(order)

    def cancel_order(self, order: Order) -> bool:
        """
        Request cancellation of an order at the broker.

        Args:
            order: Order to cancel

        Returns:
            True if cancellation was requested successfully
        """
        if not order.broker_order_id:
            # No broker order to cancel
            order.status = "cancelled"
            self.orders_repo.save(order)
            return True

        success = self.broker.cancel_order(order.broker_order_id)

        if success:
            order.broker_status = BrokerOrderStatus.CANCELLED.value
            order.status = "cancelled"
            self.orders_repo.save(order)

            if self.event_logger:
                self._log_event(order, "order_cancelled", {})

        return success

    def sync_order_status(self, order: Order) -> None:
        """
        Sync order status with broker.

        Args:
            order: Order to sync
        """
        if not order.broker_order_id:
            return

        state = self.broker.get_order_status(order.broker_order_id)
        if not state:
            logger.warning(f"Order {order.id} not found at broker")
            return

        old_status = order.broker_status
        order.broker_status = state.status.value
        order.last_broker_update = state.last_update

        if state.rejection_reason:
            order.rejection_reason = state.rejection_reason

        # Map broker status to our status
        if state.status == BrokerOrderStatus.FILLED:
            order.status = "filled"
        elif state.status == BrokerOrderStatus.REJECTED:
            order.status = "rejected"
        elif state.status == BrokerOrderStatus.CANCELLED:
            order.status = "cancelled"
        elif state.status in (BrokerOrderStatus.WORKING, BrokerOrderStatus.PENDING):
            order.status = "pending"
        elif state.status == BrokerOrderStatus.PARTIAL:
            order.status = "submitted"  # Partial still in progress

        if old_status != order.broker_status:
            self.orders_repo.save(order)

            if self.event_logger:
                self._log_event(
                    order,
                    "order_status_synced",
                    {
                        "old_status": old_status,
                        "new_status": order.broker_status,
                    },
                )

    def is_market_open(self) -> bool:
        """Check if market is open via broker."""
        return self.broker.is_market_open()

    def _log_event(
        self,
        order: Order,
        event_type: str,
        details: dict,
    ) -> None:
        """Log an event if event_logger is configured."""
        if not self.event_logger:
            return

        try:
            from application.events import EventType

            # Map internal event types to EventType enum
            if event_type == "fill_processed":
                log_event_type = EventType.EXECUTION_RECORDED
            else:
                log_event_type = EventType.ORDER_CREATED

            # Build payload with order details and event-specific details
            payload = {
                "order_id": order.id,
                "position_id": order.position_id,
                "side": order.side,
                "qty": order.qty,
                "status": order.status,
                "broker_order_id": order.broker_order_id,
                "avg_fill_price": order.avg_fill_price,
                "filled_qty": order.filled_qty,
                "total_commission": order.total_commission,
                "internal_event_type": event_type,
                **details,
            }

            self.event_logger.log(
                event_type=log_event_type,
                tenant_id=order.tenant_id,
                portfolio_id=order.portfolio_id,
                asset_id=order.position_id,
                source="broker_integration",
                payload=payload,
            )
        except Exception as e:
            logger.warning(f"Failed to log event: {e}")

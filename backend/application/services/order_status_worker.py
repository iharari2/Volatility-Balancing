# =========================
# backend/application/services/order_status_worker.py
# =========================
"""
Background worker that polls for order status updates from the broker.

This worker periodically checks pending/working orders and syncs their
status with the broker, processing any new fills.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Callable

from domain.entities.order import Order
from domain.ports.orders_repo import OrdersRepo
from domain.ports.positions_repo import PositionsRepo
from application.services.broker_integration_service import BrokerIntegrationService

logger = logging.getLogger(__name__)

# Dedicated logger for worker activity (can be configured separately)
activity_logger = logging.getLogger(f"{__name__}.activity")


class OrderStatusWorker:
    """
    Background worker for syncing order status with broker.

    Features:
    - Polls pending/working orders at configurable interval
    - Processes fills as they occur
    - Handles partial fills
    - Configurable callbacks for status changes
    """

    def __init__(
        self,
        orders_repo: OrdersRepo,
        broker_integration: BrokerIntegrationService,
        positions_repo: Optional[PositionsRepo] = None,
        poll_interval_seconds: float = 5.0,
        on_fill_callback: Optional[Callable[[Order], None]] = None,
        on_status_change_callback: Optional[Callable[[Order, str, str], None]] = None,
    ):
        """
        Initialize order status worker.

        Args:
            orders_repo: Repository for order persistence
            broker_integration: Broker integration service
            positions_repo: Repository for position lookup (to get symbol for orders)
            poll_interval_seconds: How often to poll (default 5 seconds)
            on_fill_callback: Called when an order is filled
            on_status_change_callback: Called when order status changes (order, old, new)
        """
        self.orders_repo = orders_repo
        self.broker_integration = broker_integration
        self.positions_repo = positions_repo
        self.poll_interval = poll_interval_seconds
        self.on_fill_callback = on_fill_callback
        self.on_status_change_callback = on_status_change_callback

        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Statistics for observability
        self._poll_count = 0
        self._orders_synced = 0
        self._fills_processed = 0
        self._status_changes = 0
        self._started_at: Optional[datetime] = None

    async def start(self) -> None:
        """Start the background worker."""
        if self._running:
            logger.warning("OrderStatusWorker already running")
            return

        self._running = True
        self._started_at = datetime.now(timezone.utc)
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            f"[OrderStatusWorker] STARTED - poll_interval={self.poll_interval}s, "
            f"positions_repo={'available' if self.positions_repo else 'NOT SET'}"
        )
        activity_logger.info(
            f"OrderStatusWorker started at {self._started_at.isoformat()}"
        )

    async def stop(self) -> None:
        """Stop the background worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        # Log final statistics
        runtime = ""
        if self._started_at:
            elapsed = datetime.now(timezone.utc) - self._started_at
            runtime = f", runtime={elapsed.total_seconds():.1f}s"

        logger.info(
            f"[OrderStatusWorker] STOPPED - polls={self._poll_count}, "
            f"orders_synced={self._orders_synced}, fills={self._fills_processed}, "
            f"status_changes={self._status_changes}{runtime}"
        )
        activity_logger.info(
            f"OrderStatusWorker stopped. Stats: polls={self._poll_count}, "
            f"orders_synced={self._orders_synced}, fills={self._fills_processed}"
        )

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    def get_stats(self) -> dict:
        """Get current worker statistics."""
        runtime_seconds = None
        if self._started_at:
            runtime_seconds = (datetime.now(timezone.utc) - self._started_at).total_seconds()

        return {
            "is_running": self._running,
            "poll_count": self._poll_count,
            "orders_synced": self._orders_synced,
            "fills_processed": self._fills_processed,
            "status_changes": self._status_changes,
            "poll_interval_seconds": self.poll_interval,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "runtime_seconds": runtime_seconds,
        }

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        logger.debug("[OrderStatusWorker] Poll loop started")
        while self._running:
            try:
                await self._poll_once()
            except Exception as e:
                logger.error(f"[OrderStatusWorker] Error in poll cycle #{self._poll_count}: {e}")

            await asyncio.sleep(self.poll_interval)

    async def _poll_once(self) -> None:
        """Single poll iteration - check all pending orders."""
        self._poll_count += 1

        # Get all orders that might need updates
        pending_orders = self._get_pending_orders()

        if not pending_orders:
            # Log every 12 polls (roughly every minute at 5s interval) when idle
            if self._poll_count % 12 == 0:
                activity_logger.debug(
                    f"[OrderStatusWorker] Poll #{self._poll_count}: no pending orders"
                )
            return

        activity_logger.info(
            f"[OrderStatusWorker] Poll #{self._poll_count}: checking {len(pending_orders)} pending order(s)"
        )

        for order in pending_orders:
            await self._sync_order(order)

    def _get_pending_orders(self) -> List[Order]:
        """Get orders that need status updates."""
        # Status values that indicate the order is still in progress
        pending_statuses = {"submitted", "pending", "working", "partial"}

        all_orders = self.orders_repo.list_all(limit=1000)
        return [o for o in all_orders if o.status in pending_statuses]

    async def _sync_order(self, order: Order) -> None:
        """Sync a single order with the broker."""
        if not order.broker_order_id:
            # No broker order ID means order hasn't been submitted to broker yet
            activity_logger.debug(
                f"[OrderStatusWorker] Skipping order {order.id}: no broker_order_id"
            )
            return

        old_status = order.status
        old_filled = order.filled_qty or 0.0

        activity_logger.debug(
            f"[OrderStatusWorker] Syncing order {order.id} "
            f"(broker_id={order.broker_order_id}, status={old_status}, filled={old_filled})"
        )

        try:
            # First, process any new fills
            symbol = self._get_symbol_for_order(order)
            if symbol:
                new_fills = self.broker_integration.process_fills_for_order(
                    order, symbol
                )
                if new_fills > 0:
                    self._fills_processed += new_fills
                    activity_logger.info(
                        f"[OrderStatusWorker] ORDER FILL: order_id={order.id}, "
                        f"symbol={symbol}, new_fills={new_fills}"
                    )
            else:
                activity_logger.warning(
                    f"[OrderStatusWorker] Cannot process fills for order {order.id}: symbol not found"
                )

            # Then sync overall status
            self.broker_integration.sync_order_status(order)
            self._orders_synced += 1

            # Check for callbacks
            order = self.orders_repo.get(order.id)  # Reload
            if order:
                new_status = order.status
                new_filled = order.filled_qty or 0.0

                # Log status change
                if old_status != new_status:
                    self._status_changes += 1
                    activity_logger.info(
                        f"[OrderStatusWorker] STATUS CHANGE: order_id={order.id}, "
                        f"{old_status} -> {new_status}, filled_qty={new_filled}"
                    )

                    # Status change callback
                    if self.on_status_change_callback:
                        try:
                            self.on_status_change_callback(order, old_status, new_status)
                        except Exception as e:
                            logger.error(f"Error in status change callback: {e}")

                # Fill callback (when order becomes fully filled)
                if (
                    new_status == "filled"
                    and old_status != "filled"
                    and self.on_fill_callback
                ):
                    activity_logger.info(
                        f"[OrderStatusWorker] ORDER FILLED: order_id={order.id}, "
                        f"qty={order.qty}, avg_price={order.avg_fill_price}"
                    )
                    try:
                        self.on_fill_callback(order)
                    except Exception as e:
                        logger.error(f"Error in fill callback: {e}")

        except Exception as e:
            logger.error(f"[OrderStatusWorker] Error syncing order {order.id}: {e}")

    def _get_symbol_for_order(self, order: Order) -> Optional[str]:
        """
        Get the symbol for an order.

        This looks up the position to get the asset symbol.
        Returns None if position not found or positions_repo not available.
        """
        if self.positions_repo is None:
            logger.warning("positions_repo not set - cannot look up symbol for order")
            return None

        if not order.position_id:
            return None

        try:
            # Try to get position using the order's position_id
            # We need tenant_id and portfolio_id - check if they're on the order
            tenant_id = getattr(order, "tenant_id", "default")
            portfolio_id = getattr(order, "portfolio_id", None)

            if portfolio_id:
                position = self.positions_repo.get(
                    tenant_id=tenant_id,
                    portfolio_id=portfolio_id,
                    position_id=order.position_id,
                )
            else:
                # Fallback: try to find position by ID across all portfolios
                all_positions = self.positions_repo.list_all(limit=1000)
                position = next(
                    (p for p in all_positions if p.id == order.position_id), None
                )

            if position:
                return position.symbol
        except Exception as e:
            logger.error(f"Error looking up symbol for order {order.id}: {e}")

        return None

    def poll_now(self) -> int:
        """
        Synchronous poll - useful for testing.

        Returns the number of orders processed.
        """
        pending_orders = self._get_pending_orders()
        processed = 0

        for order in pending_orders:
            if order.broker_order_id:
                old_status = order.status

                try:
                    self.broker_integration.sync_order_status(order)
                    order = self.orders_repo.get(order.id)

                    if order and order.status != old_status:
                        processed += 1

                        if self.on_status_change_callback:
                            try:
                                self.on_status_change_callback(
                                    order, old_status, order.status
                                )
                            except Exception as e:
                                logger.error(f"Error in status change callback: {e}")

                        if order.status == "filled" and self.on_fill_callback:
                            try:
                                self.on_fill_callback(order)
                            except Exception as e:
                                logger.error(f"Error in fill callback: {e}")

                except Exception as e:
                    logger.error(f"Error syncing order {order.id}: {e}")

        return processed


class OrderStatusWorkerManager:
    """
    Manager for the order status worker lifecycle.

    Use this in FastAPI lifespan events to start/stop the worker.
    """

    _instance: Optional["OrderStatusWorkerManager"] = None
    _worker: Optional[OrderStatusWorker] = None

    @classmethod
    def get_instance(cls) -> "OrderStatusWorkerManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(
        self,
        orders_repo: OrdersRepo,
        broker_integration: BrokerIntegrationService,
        positions_repo: Optional[PositionsRepo] = None,
        poll_interval_seconds: float = 5.0,
    ) -> None:
        """Initialize the worker with dependencies."""
        self._worker = OrderStatusWorker(
            orders_repo=orders_repo,
            broker_integration=broker_integration,
            positions_repo=positions_repo,
            poll_interval_seconds=poll_interval_seconds,
        )

    async def start(self) -> None:
        """Start the worker."""
        if self._worker:
            await self._worker.start()

    async def stop(self) -> None:
        """Stop the worker."""
        if self._worker:
            await self._worker.stop()

    @property
    def worker(self) -> Optional[OrderStatusWorker]:
        """Get the worker instance."""
        return self._worker

    def get_stats(self) -> Optional[dict]:
        """Get worker statistics if worker is initialized."""
        if self._worker:
            return self._worker.get_stats()
        return None

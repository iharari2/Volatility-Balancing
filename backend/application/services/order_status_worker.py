# =========================
# backend/application/services/order_status_worker.py
# =========================
"""
Order Status Worker — Producer-Consumer reconciliation loop.

Runs 3 phases each cycle:
  Phase 1: Cancel stuck "submitted/created" orders (no broker_order_id, past timeout)
  Phase 2: Sync broker-pending orders (have broker_order_id) via sync_order_status()
  Phase 3: Cancel stale DAY orders (pending past market close); GTC orders → sync only
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Callable

from domain.entities.order import Order
from domain.ports.orders_repo import OrdersRepo
from application.services.broker_integration_service import BrokerIntegrationService

logger = logging.getLogger(__name__)


def _ensure_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime is timezone-aware (assume UTC if naive)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# Statuses considered "pending" (still in-flight at broker)
PENDING_STATUSES = {"pending", "working", "partial"}

# Statuses considered "stuck submitted" (never reached broker)
STUCK_SUBMITTED_STATUSES = {"submitted", "created"}

# Default timeout for stuck submitted orders (no broker_order_id)
DEFAULT_STUCK_TIMEOUT_SECONDS = int(
    os.getenv("ORDER_STUCK_SUBMITTED_TIMEOUT_SECONDS", "300")
)

# IOC/FOK orders should resolve almost immediately
IOC_FOK_STALE_SECONDS = 60


class OrderStatusWorker:
    """
    Reconciliation worker that syncs order states with the broker.

    Constructor matches test expectations:
        OrderStatusWorker(orders_repo, broker_integration,
                          on_status_change_callback=None, on_fill_callback=None)
    """

    def __init__(
        self,
        orders_repo: OrdersRepo,
        broker_integration: BrokerIntegrationService,
        on_status_change_callback: Optional[Callable[[Order, str, str], None]] = None,
        on_fill_callback: Optional[Callable[[Order], None]] = None,
    ):
        self._orders_repo = orders_repo
        self._broker_integration = broker_integration
        self._on_status_change = on_status_change_callback
        self._on_fill = on_fill_callback
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    # ------------------------------------------------------------------
    # Public entry point — called once per TradingWorker cycle
    # ------------------------------------------------------------------

    def poll_now(self) -> int:
        """
        Run 3-phase reconciliation. Returns number of broker-synced orders.
        """
        self._is_running = True
        try:
            all_orders = list(self._orders_repo.list_all())

            # Phase 1: cancel stuck submitted orders
            self._cancel_stuck_submitted_orders(all_orders)

            # Phase 2: sync broker-pending orders
            synced = self._sync_broker_pending_orders(all_orders)

            # Phase 3: cancel stale DAY / IOC / FOK orders
            self._cancel_stale_day_orders(all_orders)

            return synced
        finally:
            self._is_running = False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_pending_orders(self) -> List[Order]:
        """Return orders in pending/working/partial status."""
        all_orders = list(self._orders_repo.list_all())
        return [o for o in all_orders if o.status in PENDING_STATUSES]

    # ------------------------------------------------------------------
    # Phase 1 — stuck submitted (no broker_order_id past timeout)
    # ------------------------------------------------------------------

    def _cancel_stuck_submitted_orders(self, all_orders: List[Order]) -> None:
        now = datetime.now(timezone.utc)
        timeout = timedelta(seconds=DEFAULT_STUCK_TIMEOUT_SECONDS)

        for order in all_orders:
            if order.status not in STUCK_SUBMITTED_STATUSES:
                continue
            if order.broker_order_id:
                continue  # has broker id — not stuck
            age = now - _ensure_aware(order.created_at)
            if age < timeout:
                continue

            logger.info(
                f"Auto-cancelling stuck submitted order {order.id} "
                f"(age={age}, no broker_order_id)"
            )
            try:
                self._broker_integration.cancel_order(order)
            except Exception:
                logger.exception(f"Error cancelling stuck order {order.id}")

    # ------------------------------------------------------------------
    # Phase 2 — sync broker-pending orders
    # ------------------------------------------------------------------

    def _sync_broker_pending_orders(self, all_orders: List[Order]) -> int:
        synced = 0

        for order in all_orders:
            if order.status not in PENDING_STATUSES:
                continue
            if not order.broker_order_id:
                continue  # nothing to sync

            old_status = order.status

            try:
                self._broker_integration.sync_order_status(order)
            except Exception:
                logger.exception(
                    f"Error syncing order {order.id} (broker_id={order.broker_order_id})"
                )
                continue

            # Re-read from repo to get the updated status
            updated_order = self._orders_repo.get(order.id)
            if updated_order is None:
                continue

            synced += 1

            if updated_order.status != old_status:
                if self._on_status_change:
                    self._on_status_change(updated_order, old_status, updated_order.status)

                if updated_order.status == "filled" and self._on_fill:
                    self._on_fill(updated_order)

        return synced

    # ------------------------------------------------------------------
    # Phase 3 — stale DAY / IOC / FOK orders
    # ------------------------------------------------------------------

    def _cancel_stale_day_orders(self, all_orders: List[Order]) -> None:
        now = datetime.now(timezone.utc)

        for order in all_orders:
            if order.status not in PENDING_STATUSES:
                continue
            if not order.broker_order_id:
                continue

            tif = (order.time_in_force or "day").lower()

            if tif == "day":
                # DAY orders pending from a previous trading day should be cancelled
                if not self._is_stale_day_order(order, now):
                    continue
                logger.info(
                    f"Auto-cancelling stale DAY order {order.id} "
                    f"(submitted_to_broker_at={order.submitted_to_broker_at})"
                )
                try:
                    self._broker_integration.cancel_order(order)
                except Exception:
                    logger.exception(f"Error cancelling stale DAY order {order.id}")

            elif tif in ("ioc", "fok"):
                # IOC/FOK should fill/reject almost immediately
                submitted_at = _ensure_aware(order.submitted_to_broker_at or order.created_at)
                age = now - submitted_at
                if age.total_seconds() > IOC_FOK_STALE_SECONDS:
                    logger.info(
                        f"Auto-cancelling stale {tif.upper()} order {order.id} "
                        f"(age={age})"
                    )
                    try:
                        self._broker_integration.cancel_order(order)
                    except Exception:
                        logger.exception(
                            f"Error cancelling stale {tif.upper()} order {order.id}"
                        )

            # GTC orders — never auto-cancel, broker sync only (handled in Phase 2)

    def _is_stale_day_order(self, order: Order, now: datetime) -> bool:
        """
        A DAY order is stale if:
        - Market is not open AND
        - It was submitted on a previous calendar day
        """
        submitted_at = _ensure_aware(order.submitted_to_broker_at or order.created_at)
        submitted_date = submitted_at.date()
        today = now.date()

        if submitted_date >= today:
            return False  # Same day — not stale yet

        # Submitted on a previous day, check if market is closed
        try:
            if not self._broker_integration.is_market_open():
                return True
        except Exception:
            logger.exception("Error checking market hours for stale order detection")

        return False

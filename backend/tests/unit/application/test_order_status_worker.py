# =========================
# backend/tests/unit/application/test_order_status_worker.py
# =========================
"""Unit tests for OrderStatusWorker."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from application.services.order_status_worker import OrderStatusWorker
from domain.entities.order import Order
from domain.ports.broker_service import BrokerOrderStatus


class TestOrderStatusWorker:
    """Test suite for OrderStatusWorker."""

    def create_order(
        self,
        order_id: str = "ord_001",
        status: str = "pending",
        broker_order_id: str = None,
        filled_qty: float = 0.0,
    ) -> Order:
        """Create a test order."""
        return Order(
            id=order_id,
            position_id="pos_001",
            tenant_id="default",
            portfolio_id="test",
            side="BUY",
            qty=100.0,
            status=status,
            broker_order_id=broker_order_id,
            filled_qty=filled_qty,
            created_at=datetime.now(timezone.utc),
        )

    def test_get_pending_orders_filters_correctly(self):
        """Test that pending orders are correctly identified."""
        # Create mock orders repo with various statuses
        orders = [
            self.create_order("ord_001", "pending", "broker_001"),
            self.create_order("ord_002", "working", "broker_002"),
            self.create_order("ord_003", "filled"),  # Should not be included
            self.create_order("ord_004", "cancelled"),  # Should not be included
            self.create_order("ord_005", "partial", "broker_005"),
        ]

        orders_repo = Mock()
        orders_repo.list_all.return_value = orders

        broker_integration = Mock()

        worker = OrderStatusWorker(
            orders_repo=orders_repo,
            broker_integration=broker_integration,
        )

        pending = worker._get_pending_orders()

        # Should include pending, working, and partial
        assert len(pending) == 3
        assert any(o.id == "ord_001" for o in pending)
        assert any(o.id == "ord_002" for o in pending)
        assert any(o.id == "ord_005" for o in pending)

    def test_poll_now_syncs_orders(self):
        """Test that poll_now syncs orders with broker."""
        order = self.create_order("ord_001", "working", "broker_001")
        updated_order = self.create_order("ord_001", "filled", "broker_001", 100.0)

        orders_repo = Mock()
        orders_repo.list_all.return_value = [order]
        orders_repo.get.return_value = updated_order

        broker_integration = Mock()

        callback_called = []

        def on_status_change(order, old_status, new_status):
            callback_called.append((order.id, old_status, new_status))

        worker = OrderStatusWorker(
            orders_repo=orders_repo,
            broker_integration=broker_integration,
            on_status_change_callback=on_status_change,
        )

        processed = worker.poll_now()

        assert processed == 1
        broker_integration.sync_order_status.assert_called_once()
        assert len(callback_called) == 1
        assert callback_called[0] == ("ord_001", "working", "filled")

    def test_poll_now_calls_fill_callback(self):
        """Test that fill callback is called when order becomes filled."""
        order = self.create_order("ord_001", "working", "broker_001")
        filled_order = self.create_order("ord_001", "filled", "broker_001", 100.0)

        orders_repo = Mock()
        orders_repo.list_all.return_value = [order]
        orders_repo.get.return_value = filled_order

        broker_integration = Mock()

        fill_callback_called = []

        def on_fill(order):
            fill_callback_called.append(order.id)

        worker = OrderStatusWorker(
            orders_repo=orders_repo,
            broker_integration=broker_integration,
            on_fill_callback=on_fill,
        )

        worker.poll_now()

        assert len(fill_callback_called) == 1
        assert fill_callback_called[0] == "ord_001"

    def test_poll_now_skips_orders_without_broker_id(self):
        """Test that orders without broker_order_id are skipped."""
        order = self.create_order("ord_001", "pending")  # No broker_order_id

        orders_repo = Mock()
        orders_repo.list_all.return_value = [order]

        broker_integration = Mock()

        worker = OrderStatusWorker(
            orders_repo=orders_repo,
            broker_integration=broker_integration,
        )

        processed = worker.poll_now()

        assert processed == 0
        broker_integration.sync_order_status.assert_not_called()

    def test_poll_now_handles_sync_errors(self):
        """Test that sync errors are handled gracefully."""
        order = self.create_order("ord_001", "working", "broker_001")

        orders_repo = Mock()
        orders_repo.list_all.return_value = [order]

        broker_integration = Mock()
        broker_integration.sync_order_status.side_effect = Exception("Broker error")

        worker = OrderStatusWorker(
            orders_repo=orders_repo,
            broker_integration=broker_integration,
        )

        # Should not raise
        processed = worker.poll_now()

        assert processed == 0

    def test_worker_is_running_property(self):
        """Test is_running property."""
        orders_repo = Mock()
        broker_integration = Mock()

        worker = OrderStatusWorker(
            orders_repo=orders_repo,
            broker_integration=broker_integration,
        )

        assert worker.is_running is False

# =========================
# backend/tests/integration/test_orders_cancel_status.py
# =========================
"""Integration tests for order cancel and status endpoints."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.di import container
from domain.entities.position import Position
from domain.entities.order import Order
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def reset_container():
    """Reset container state before each test."""
    container.reset()
    yield


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_position():
    """Create a sample position."""
    position = Position(
        id="pos_test",
        tenant_id="default",
        portfolio_id="test",
        asset_symbol="AAPL",
        qty=100.0,
        cash=10000.0,
        anchor_price=150.0,
    )
    container.positions.save(position)
    return position


@pytest.fixture
def sample_order(sample_position):
    """Create a sample order."""
    order = Order(
        id="ord_test_001",
        position_id=sample_position.id,
        tenant_id=sample_position.tenant_id,
        portfolio_id=sample_position.portfolio_id,
        side="BUY",
        qty=10.0,
        status="pending",
        broker_order_id="stub_abc123",
        broker_status="working",
        created_at=datetime.now(timezone.utc),
    )
    container.orders.save(order)
    return order


class TestCancelOrderEndpoint:
    """Test suite for POST /v1/orders/{order_id}/cancel."""

    def test_cancel_pending_order_success(self, client, sample_position):
        """Test cancelling a pending order without broker submission."""
        # Create an order that wasn't submitted to broker (no broker_order_id)
        order = Order(
            id="ord_cancel_test",
            position_id=sample_position.id,
            tenant_id=sample_position.tenant_id,
            portfolio_id=sample_position.portfolio_id,
            side="BUY",
            qty=10.0,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        container.orders.save(order)

        response = client.post("/v1/orders/ord_cancel_test/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == "ord_cancel_test"
        assert data["cancelled"] is True
        assert data["status"] == "cancelled"

    def test_cancel_broker_submitted_order_not_found(self, client, sample_order):
        """Test cancelling order that broker doesn't know about returns failure."""
        # sample_order has broker_order_id but stub broker doesn't have it
        response = client.post(f"/v1/orders/{sample_order.id}/cancel")

        assert response.status_code == 200
        data = response.json()
        # Broker couldn't cancel because it doesn't know about the order
        assert data["cancelled"] is False
        assert "Broker could not cancel" in data["message"]

    def test_cancel_filled_order_fails(self, client, sample_position):
        """Test that filled orders cannot be cancelled."""
        # Create a filled order
        order = Order(
            id="ord_filled",
            position_id=sample_position.id,
            tenant_id=sample_position.tenant_id,
            portfolio_id=sample_position.portfolio_id,
            side="BUY",
            qty=10.0,
            status="filled",
            filled_qty=10.0,
            created_at=datetime.now(timezone.utc),
        )
        container.orders.save(order)

        response = client.post("/v1/orders/ord_filled/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["cancelled"] is False
        assert data["status"] == "filled"
        assert "already filled" in data["message"]

    def test_cancel_nonexistent_order_404(self, client):
        """Test that cancelling nonexistent order returns 404."""
        response = client.post("/v1/orders/nonexistent/cancel")

        assert response.status_code == 404
        assert response.json()["detail"] == "order_not_found"

    def test_cancel_rejected_order_fails(self, client, sample_position):
        """Test that rejected orders cannot be cancelled."""
        order = Order(
            id="ord_rejected",
            position_id=sample_position.id,
            tenant_id=sample_position.tenant_id,
            portfolio_id=sample_position.portfolio_id,
            side="BUY",
            qty=10.0,
            status="rejected",
            rejection_reason="Test rejection",
            created_at=datetime.now(timezone.utc),
        )
        container.orders.save(order)

        response = client.post("/v1/orders/ord_rejected/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["cancelled"] is False
        assert data["status"] == "rejected"


class TestOrderStatusEndpoint:
    """Test suite for GET /v1/orders/{order_id}/status."""

    def test_get_order_status_success(self, client, sample_order):
        """Test getting order status."""
        response = client.get(f"/v1/orders/{sample_order.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == sample_order.id
        assert data["position_id"] == sample_order.position_id
        assert data["side"] == "BUY"
        assert data["qty"] == 10.0
        assert data["status"] == "pending"
        assert data["broker_order_id"] == "stub_abc123"
        assert data["broker_status"] == "working"

    def test_get_order_status_with_fill_info(self, client, sample_position):
        """Test getting status of partially filled order."""
        order = Order(
            id="ord_partial",
            position_id=sample_position.id,
            tenant_id=sample_position.tenant_id,
            portfolio_id=sample_position.portfolio_id,
            side="BUY",
            qty=100.0,
            status="partial",
            broker_order_id="stub_xyz789",
            broker_status="partial",
            filled_qty=50.0,
            avg_fill_price=150.0,
            total_commission=7.50,
            created_at=datetime.now(timezone.utc),
        )
        container.orders.save(order)

        response = client.get("/v1/orders/ord_partial/status")

        assert response.status_code == 200
        data = response.json()
        assert data["filled_qty"] == 50.0
        assert data["avg_fill_price"] == 150.0
        assert data["total_commission"] == 7.50
        assert data["status"] == "partial"

    def test_get_order_status_nonexistent_404(self, client):
        """Test that nonexistent order returns 404."""
        response = client.get("/v1/orders/nonexistent/status")

        assert response.status_code == 404
        assert response.json()["detail"] == "order_not_found"

    def test_get_order_status_with_rejection(self, client, sample_position):
        """Test getting status of rejected order."""
        order = Order(
            id="ord_rejected_status",
            position_id=sample_position.id,
            tenant_id=sample_position.tenant_id,
            portfolio_id=sample_position.portfolio_id,
            side="SELL",
            qty=10.0,
            status="rejected",
            rejection_reason="Insufficient buying power",
            created_at=datetime.now(timezone.utc),
        )
        container.orders.save(order)

        response = client.get("/v1/orders/ord_rejected_status/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "Insufficient buying power"

# =========================
# backend/tests/unit/infrastructure/test_stub_broker_adapter.py
# =========================
"""Unit tests for StubBrokerAdapter."""

import pytest
from decimal import Decimal

from infrastructure.adapters.stub_broker_adapter import StubBrokerAdapter
from domain.ports.broker_service import (
    BrokerOrderRequest,
    BrokerOrderStatus,
)


class TestStubBrokerAdapter:
    """Test suite for StubBrokerAdapter."""

    def test_immediate_fill_mode_fills_order_instantly(self):
        """Test that immediate fill mode fills orders right away."""
        broker = StubBrokerAdapter(fill_mode="immediate")
        broker.set_price("AAPL", Decimal("150.00"))

        request = BrokerOrderRequest(
            client_order_id="ord_001",
            symbol="AAPL",
            side="buy",
            qty=Decimal("10"),
        )

        response = broker.submit_order(request)

        assert response.status == BrokerOrderStatus.FILLED
        assert response.broker_order_id.startswith("stub_")
        assert response.client_order_id == "ord_001"

    def test_delayed_fill_mode_stays_working(self):
        """Test that delayed fill mode keeps orders in working state."""
        broker = StubBrokerAdapter(fill_mode="delayed")
        broker.set_price("AAPL", Decimal("150.00"))

        request = BrokerOrderRequest(
            client_order_id="ord_002",
            symbol="AAPL",
            side="buy",
            qty=Decimal("10"),
        )

        response = broker.submit_order(request)

        assert response.status == BrokerOrderStatus.WORKING
        assert response.broker_order_id.startswith("stub_")

    def test_reject_mode_rejects_all_orders(self):
        """Test that reject mode rejects all orders."""
        broker = StubBrokerAdapter(fill_mode="reject")

        request = BrokerOrderRequest(
            client_order_id="ord_003",
            symbol="AAPL",
            side="buy",
            qty=Decimal("10"),
        )

        response = broker.submit_order(request)

        assert response.status == BrokerOrderStatus.REJECTED
        assert "reject mode" in response.message.lower()

    def test_advance_order_fills_delayed_order(self):
        """Test that advance_order fills a delayed order."""
        broker = StubBrokerAdapter(fill_mode="delayed")
        broker.set_price("AAPL", Decimal("150.00"))

        request = BrokerOrderRequest(
            client_order_id="ord_004",
            symbol="AAPL",
            side="buy",
            qty=Decimal("10"),
        )

        response = broker.submit_order(request)
        assert response.status == BrokerOrderStatus.WORKING

        # Advance the order
        success = broker.advance_order(response.broker_order_id)
        assert success

        # Check status is now filled
        state = broker.get_order_status(response.broker_order_id)
        assert state.status == BrokerOrderStatus.FILLED

    def test_get_fills_returns_fill_details(self):
        """Test that get_fills returns correct fill information."""
        broker = StubBrokerAdapter(fill_mode="immediate")
        broker.set_price("AAPL", Decimal("150.00"))

        request = BrokerOrderRequest(
            client_order_id="ord_005",
            symbol="AAPL",
            side="buy",
            qty=Decimal("10"),
        )

        response = broker.submit_order(request)
        fills = broker.get_fills(response.broker_order_id)

        assert len(fills) == 1
        fill = fills[0]
        assert fill.fill_qty == Decimal("10")
        assert fill.fill_price == Decimal("150.00")
        assert fill.commission >= Decimal("0.01")  # Min commission

    def test_commission_calculation(self):
        """Test that commission is calculated correctly."""
        broker = StubBrokerAdapter(
            fill_mode="immediate",
            commission_rate=Decimal("0.001"),  # 0.1%
            min_commission=Decimal("0.01"),
        )
        broker.set_price("AAPL", Decimal("100.00"))

        request = BrokerOrderRequest(
            client_order_id="ord_006",
            symbol="AAPL",
            side="buy",
            qty=Decimal("100"),  # $10,000 notional
        )

        response = broker.submit_order(request)
        fills = broker.get_fills(response.broker_order_id)

        # $10,000 * 0.1% = $10 commission
        assert fills[0].commission == Decimal("10.00")

    def test_min_commission_applied(self):
        """Test that minimum commission is applied for small orders."""
        broker = StubBrokerAdapter(
            fill_mode="immediate",
            commission_rate=Decimal("0.001"),
            min_commission=Decimal("1.00"),
        )
        broker.set_price("AAPL", Decimal("10.00"))

        request = BrokerOrderRequest(
            client_order_id="ord_007",
            symbol="AAPL",
            side="buy",
            qty=Decimal("1"),  # $10 notional, 0.1% = $0.01
        )

        response = broker.submit_order(request)
        fills = broker.get_fills(response.broker_order_id)

        # Min commission of $1.00 should be applied
        assert fills[0].commission == Decimal("1.00")

    def test_cancel_order_success(self):
        """Test that cancel_order works for working orders."""
        broker = StubBrokerAdapter(fill_mode="delayed")
        broker.set_price("AAPL", Decimal("150.00"))

        request = BrokerOrderRequest(
            client_order_id="ord_008",
            symbol="AAPL",
            side="buy",
            qty=Decimal("10"),
        )

        response = broker.submit_order(request)
        success = broker.cancel_order(response.broker_order_id)

        assert success
        state = broker.get_order_status(response.broker_order_id)
        assert state.status == BrokerOrderStatus.CANCELLED

    def test_cancel_filled_order_fails(self):
        """Test that cancel_order fails for filled orders."""
        broker = StubBrokerAdapter(fill_mode="immediate")
        broker.set_price("AAPL", Decimal("150.00"))

        request = BrokerOrderRequest(
            client_order_id="ord_009",
            symbol="AAPL",
            side="buy",
            qty=Decimal("10"),
        )

        response = broker.submit_order(request)
        success = broker.cancel_order(response.broker_order_id)

        assert not success

    def test_is_market_open_default(self):
        """Test that is_market_open returns True by default."""
        broker = StubBrokerAdapter(simulate_market_hours=False)
        assert broker.is_market_open() is True

    def test_get_order_status_not_found(self):
        """Test that get_order_status returns None for unknown orders."""
        broker = StubBrokerAdapter()
        state = broker.get_order_status("nonexistent")
        assert state is None

    def test_partial_fill(self):
        """Test partial fill functionality."""
        broker = StubBrokerAdapter(fill_mode="delayed")
        broker.set_price("AAPL", Decimal("150.00"))

        request = BrokerOrderRequest(
            client_order_id="ord_010",
            symbol="AAPL",
            side="buy",
            qty=Decimal("100"),
        )

        response = broker.submit_order(request)

        # Partial fill of 30 shares
        broker.advance_order(response.broker_order_id, partial_qty=Decimal("30"))
        state = broker.get_order_status(response.broker_order_id)

        assert state.status == BrokerOrderStatus.PARTIAL
        assert state.filled_qty == Decimal("30")

        # Fill remaining 70 shares
        broker.advance_order(response.broker_order_id)
        state = broker.get_order_status(response.broker_order_id)

        assert state.status == BrokerOrderStatus.FILLED
        assert state.filled_qty == Decimal("100")

    def test_reset_clears_all_state(self):
        """Test that reset clears all orders and fills."""
        broker = StubBrokerAdapter(fill_mode="immediate")
        broker.set_price("AAPL", Decimal("150.00"))

        request = BrokerOrderRequest(
            client_order_id="ord_011",
            symbol="AAPL",
            side="buy",
            qty=Decimal("10"),
        )

        response = broker.submit_order(request)
        broker.reset()

        # All data should be cleared
        state = broker.get_order_status(response.broker_order_id)
        assert state is None
        fills = broker.get_fills(response.broker_order_id)
        assert fills == []

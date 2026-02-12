# =========================
# backend/tests/integration/test_alpaca_broker.py
# =========================
"""
Integration tests for Alpaca broker adapter.

These tests require valid Alpaca credentials in paper trading mode.
Run with: pytest tests/integration/test_alpaca_broker.py -v

Environment variables required:
    ALPACA_API_KEY: Your Alpaca API key
    ALPACA_SECRET_KEY: Your Alpaca secret key
    ALPACA_PAPER: Should be "true" for these tests
"""

import os
import pytest
from decimal import Decimal
from datetime import datetime

# Skip all tests if alpaca-py is not installed
alpaca = pytest.importorskip("alpaca", reason="alpaca-py not installed")


def has_alpaca_credentials() -> bool:
    """Check if Alpaca credentials are configured."""
    return bool(
        os.getenv("ALPACA_API_KEY") and os.getenv("ALPACA_SECRET_KEY")
    )


@pytest.fixture
def alpaca_adapter():
    """Create an Alpaca adapter with credentials from environment."""
    if not has_alpaca_credentials():
        pytest.skip("Alpaca credentials not configured")

    from infrastructure.config.broker_credentials import AlpacaCredentials
    from infrastructure.adapters.alpaca_broker_adapter import AlpacaBrokerAdapter

    # Force paper trading for tests
    os.environ["ALPACA_PAPER"] = "true"

    creds = AlpacaCredentials.from_env()
    assert creds.paper, "Tests must run in paper trading mode"

    return AlpacaBrokerAdapter(creds)


@pytest.mark.skipif(
    not has_alpaca_credentials(),
    reason="Alpaca credentials not configured",
)
class TestAlpacaBrokerIntegration:
    """Integration tests for Alpaca broker adapter."""

    def test_connection_and_account(self, alpaca_adapter):
        """Test that we can connect and get account info."""
        account = alpaca_adapter.get_account()

        assert "buying_power" in account
        assert "cash" in account
        assert "status" in account
        assert account["status"] == "ACTIVE"

    def test_market_hours(self, alpaca_adapter):
        """Test getting market hours."""
        hours = alpaca_adapter.get_market_hours()

        assert hours is not None
        assert isinstance(hours.is_open, bool)
        assert isinstance(hours.current_time, datetime)
        assert hours.session in ("regular", "closed", "unknown")

    def test_is_market_open(self, alpaca_adapter):
        """Test checking if market is open."""
        is_open = alpaca_adapter.is_market_open()
        assert isinstance(is_open, bool)

    def test_get_positions(self, alpaca_adapter):
        """Test getting current positions."""
        positions = alpaca_adapter.get_positions()

        assert isinstance(positions, list)
        # Each position should have required fields
        for pos in positions:
            assert "symbol" in pos
            assert "qty" in pos
            assert "market_value" in pos

    @pytest.mark.skip(reason="Actually submits orders - run manually")
    def test_submit_and_cancel_order(self, alpaca_adapter):
        """
        Test submitting and cancelling an order.

        WARNING: This test actually submits an order to Alpaca paper trading.
        Only run manually when you want to test the full order flow.
        """
        from domain.ports.broker_service import BrokerOrderRequest, BrokerOrderStatus

        # Submit a small limit order well below market price (won't fill)
        request = BrokerOrderRequest(
            client_order_id=f"test_{datetime.now().timestamp()}",
            symbol="AAPL",
            side="buy",
            qty=Decimal("1"),
            order_type="limit",
            limit_price=Decimal("1.00"),  # Way below market, won't fill
        )

        response = alpaca_adapter.submit_order(request)

        assert response.broker_order_id is not None
        assert response.status in (
            BrokerOrderStatus.PENDING,
            BrokerOrderStatus.WORKING,
        )

        # Cancel the order
        cancelled = alpaca_adapter.cancel_order(response.broker_order_id)
        assert cancelled is True

        # Verify it's cancelled
        status = alpaca_adapter.get_order_status(response.broker_order_id)
        assert status is not None
        assert status.status == BrokerOrderStatus.CANCELLED


@pytest.mark.skipif(
    not has_alpaca_credentials(),
    reason="Alpaca credentials not configured",
)
class TestAlpacaStatusMapping:
    """Test Alpaca status mapping."""

    def test_status_mapping_exists(self, alpaca_adapter):
        """Verify status mapping covers all expected statuses."""
        from alpaca.trading.enums import OrderStatus as AlpacaOrderStatus
        from domain.ports.broker_service import BrokerOrderStatus

        # Ensure we can map all Alpaca statuses
        for alpaca_status in AlpacaOrderStatus:
            broker_status = alpaca_adapter._map_order_status(alpaca_status)
            assert isinstance(broker_status, BrokerOrderStatus)

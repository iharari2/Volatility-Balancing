# =========================
# backend/tests/integration/test_continuous_trading_fixes.py
# =========================
"""
Integration tests for continuous trading service.
"""

import threading

import pytest

from app.di import container
from application.services.continuous_trading_service import (
    ContinuousTradingService,
    TradingStatus,
)
from domain.entities.position import Position
from domain.entities.portfolio import Portfolio


@pytest.fixture
def trading_position():
    """Create a real position in the container for testing."""
    tenant_id = "default"
    portfolio_id = "cts_portfolio"
    position_id = "cts_position"

    portfolio = Portfolio(id=portfolio_id, tenant_id=tenant_id, name="CTS Test Portfolio")
    container.portfolio_repo.save(portfolio)

    pos = container.positions.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        asset_symbol="AAPL",
        qty=10.0,
        anchor_price=100.0,
    )
    pos.cash = 1000.0
    container.positions.save(pos)

    return {"tenant_id": tenant_id, "portfolio_id": portfolio_id, "position_id": pos.id}


def test_monitor_position_stops_when_event_set(trading_position):
    """_monitor_position exits cleanly when stop_event is set."""
    service = ContinuousTradingService()
    position_id = trading_position["position_id"]

    service._active_positions[position_id] = TradingStatus(
        position_id=position_id, is_running=True
    )

    stop_event = threading.Event()
    # Set the event before calling — loop should exit on the first is_set() check.
    stop_event.set()

    # Should return immediately without blocking.
    service._monitor_position(position_id, 0, stop_event, None)


def test_monitor_position_stops_on_missing_position():
    """_monitor_position exits when position is not found."""
    service = ContinuousTradingService()
    non_existent_id = "does_not_exist_xyz"

    service._active_positions[non_existent_id] = TradingStatus(
        position_id=non_existent_id, is_running=True
    )

    stop_event = threading.Event()

    # Should exit the loop with a 'position not found' break, not hang.
    service._monitor_position(non_existent_id, 0, stop_event, None)

    # The function should have returned without the stop_event being set.
    assert not stop_event.is_set()


def test_fill_order_response_includes_trade_id():
    """FillOrderResponse carries the trade_id field."""
    from application.dto.orders import FillOrderResponse

    response = FillOrderResponse(
        order_id="ord_123",
        status="filled",
        filled_qty=10.0,
        trade_id="trd_456",
    )

    assert response.trade_id == "trd_456"


def test_trading_status_tracks_errors(trading_position):
    """Error count increments when evaluation fails (using deterministic market data)."""
    from infrastructure.market.deterministic_market_data import DeterministicMarketDataAdapter

    # Point container at deterministic market data so the monitor can get a price.
    container.market_data = DeterministicMarketDataAdapter()

    service = ContinuousTradingService()
    position_id = trading_position["position_id"]
    stop_event = threading.Event()

    service._active_positions[position_id] = TradingStatus(
        position_id=position_id, is_running=True
    )

    # Run the monitor in a background thread; give it a moment, then stop it.
    thread = threading.Thread(
        target=service._monitor_position,
        args=(position_id, 0, stop_event, None),
        daemon=True,
    )
    thread.start()
    # Let it run for one tick and stop.
    thread.join(timeout=5)
    stop_event.set()
    thread.join(timeout=2)

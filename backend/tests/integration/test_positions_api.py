# =========================
# backend/tests/integration/test_positions_api.py
# =========================
import pytest
from datetime import datetime, timezone
from starlette.testclient import TestClient
from app.main import app
from app.di import container


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def position_id(client):
    """Create a test position and return its ID."""
    response = client.post(
        "/v1/positions",
        json={"ticker": "AAPL", "qty": 100.0, "cash": 10000.0, "anchor_price": 150.0},
    )
    assert response.status_code == 201
    return response.json()["id"]


class TestPositionsAPI:
    """Integration tests for positions API endpoints."""

    def test_create_position_success(self, client):
        """Test successful position creation."""
        response = client.post(
            "/v1/positions",
            json={"ticker": "AAPL", "qty": 100.0, "cash": 10000.0, "anchor_price": 150.0},
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["ticker"] == "AAPL"
        assert data["qty"] == 100.0
        assert data["cash"] == 10000.0
        assert data["anchor_price"] == 150.0

    def test_create_position_with_order_policy(self, client):
        """Test position creation with custom order policy."""
        response = client.post(
            "/v1/positions",
            json={
                "ticker": "MSFT",
                "qty": 50.0,
                "cash": 5000.0,
                "order_policy": {
                    "min_qty": 1.0,
                    "min_notional": 100.0,
                    "trigger_threshold_pct": 0.05,
                    "rebalance_ratio": 2.0,
                    "commission_rate": 0.001,
                    "allow_after_hours": True,
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["ticker"] == "MSFT"

    def test_create_position_invalid_order_policy(self, client):
        """Test position creation with invalid order policy."""
        response = client.post(
            "/v1/positions",
            json={
                "ticker": "GOOGL",
                "qty": 10.0,
                "cash": 2000.0,
                "order_policy": {"action_below_min": "invalid_action"},
            },
        )

        assert response.status_code == 422
        assert "Unsupported action_below_min" in response.json()["detail"]

    def test_create_position_updates_existing(self, client):
        """Test that creating position with same ticker updates existing."""
        # Create first position
        response1 = client.post(
            "/v1/positions", json={"ticker": "TSLA", "qty": 10.0, "cash": 5000.0}
        )
        assert response1.status_code == 201
        pos_id1 = response1.json()["id"]

        # Create second position with same ticker
        response2 = client.post(
            "/v1/positions", json={"ticker": "TSLA", "qty": 20.0, "cash": 8000.0}
        )
        assert response2.status_code == 201
        pos_id2 = response2.json()["id"]

        # Should be the same position ID
        assert pos_id1 == pos_id2
        assert response2.json()["qty"] == 20.0
        assert response2.json()["cash"] == 8000.0

    def test_list_positions(self, client, position_id):
        """Test listing all positions."""
        response = client.get("/v1/positions")

        assert response.status_code == 200
        data = response.json()
        assert "positions" in data
        assert len(data["positions"]) >= 1

        # Find our test position
        test_pos = next((p for p in data["positions"] if p["id"] == position_id), None)
        assert test_pos is not None
        assert test_pos["ticker"] == "AAPL"

    def test_get_position_success(self, client, position_id):
        """Test getting a specific position."""
        response = client.get(f"/v1/positions/{position_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == position_id
        assert data["ticker"] == "AAPL"
        assert "order_policy" in data
        assert "guardrails" in data

    def test_get_position_not_found(self, client):
        """Test getting non-existent position."""
        response = client.get("/v1/positions/non_existent_id")

        assert response.status_code == 404
        assert response.json()["detail"] == "position_not_found"

    def test_set_anchor_price_success(self, client, position_id):
        """Test setting anchor price."""
        response = client.post(f"/v1/positions/{position_id}/anchor?price=160.0")

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id
        assert data["anchor_price"] == 160.0
        assert "message" in data

    def test_set_anchor_price_not_found(self, client):
        """Test setting anchor price for non-existent position."""
        response = client.post("/v1/positions/non_existent_id/anchor?price=160.0")

        assert response.status_code == 404
        assert response.json()["detail"] == "position_not_found"

    def test_evaluate_position_success(self, client, position_id):
        """Test position evaluation with manual price."""
        response = client.post(f"/v1/positions/{position_id}/evaluate?current_price=145.0")

        assert response.status_code == 200
        data = response.json()
        assert "trigger_detected" in data
        assert "current_price" in data
        assert data["current_price"] == 145.0

    def test_evaluate_position_not_found(self, client):
        """Test evaluating non-existent position."""
        response = client.post("/v1/positions/non_existent_id/evaluate?current_price=145.0")

        assert response.status_code == 404
        assert response.json()["detail"] == "position_not_found"

    def test_evaluate_position_with_market_data(self, client, position_id):
        """Test position evaluation with market data."""
        response = client.post(f"/v1/positions/{position_id}/evaluate/market")

        # This might fail if market data is not available, but should not be 404
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "trigger_detected" in data

    def test_list_events(self, client, position_id):
        """Test listing events for a position."""
        response = client.get(f"/v1/positions/{position_id}/events")

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id
        assert "events" in data
        assert isinstance(data["events"], list)

    def test_list_events_with_limit(self, client, position_id):
        """Test listing events with limit."""
        response = client.get(f"/v1/positions/{position_id}/events?limit=50")

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id
        assert "events" in data

    def test_clear_all_positions(self, client, position_id):
        """Test clearing all positions."""
        # Verify position exists
        response = client.get(f"/v1/positions/{position_id}")
        assert response.status_code == 200

        # Clear all positions
        response = client.post("/v1/clear-positions")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["count"] == 0

        # Verify position no longer exists
        response = client.get(f"/v1/positions/{position_id}")
        assert response.status_code == 404

    def test_market_status(self, client):
        """Test getting market status."""
        response = client.get("/v1/market/status")

        assert response.status_code == 200
        data = response.json()
        assert "is_open" in data
        assert "timezone" in data

    def test_get_market_price_success(self, client):
        """Test getting market price for a ticker."""
        response = client.get("/v1/market/price/AAPL")

        # This might fail if market data is not available
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["ticker"] == "AAPL"
            assert "price" in data
            assert "timestamp" in data

    def test_get_market_price_not_found(self, client):
        """Test getting market price for non-existent ticker."""
        response = client.get("/v1/market/price/NONEXISTENT")

        assert response.status_code == 404
        assert response.json()["detail"] == "ticker_not_found"

    def test_get_historical_data(self, client):
        """Test getting historical data."""
        start_date = "2024-01-01T00:00:00Z"
        end_date = "2024-01-31T23:59:59Z"

        response = client.get(
            f"/v1/market/historical/AAPL?start_date={start_date}&end_date={end_date}"
        )

        # This might fail if market data is not available
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["ticker"] == "AAPL"
            assert data["start_date"] == start_date
            assert data["end_date"] == end_date
            assert "price_data" in data

    def test_run_simulation(self, client):
        """Test running a simulation."""
        request_data = {
            "ticker": "AAPL",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "initial_cash": 10000.0,
            "include_after_hours": False,
        }

        response = client.post("/v1/simulation/run", json=request_data)

        # This might fail if market data is not available
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["ticker"] == "AAPL"
            assert "algorithm" in data
            assert "buy_hold" in data
            assert "comparison" in data

    def test_get_volatility_data(self, client):
        """Test getting volatility data."""
        response = client.get("/v1/simulation/volatility/AAPL?window_minutes=60")

        # This might fail if market data is not available
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["ticker"] == "AAPL"
            assert "volatility" in data
            assert "timestamp" in data

    def test_auto_size_order_success(self, client, position_id):
        """Test auto-sizing an order."""
        response = client.post(f"/v1/positions/{position_id}/orders/auto-size?current_price=145.0")

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id
        assert data["current_price"] == 145.0
        assert "order_submitted" in data
        assert "evaluation" in data

    def test_auto_size_order_not_found(self, client):
        """Test auto-sizing order for non-existent position."""
        response = client.post("/v1/positions/non_existent_id/orders/auto-size?current_price=145.0")

        assert response.status_code == 404
        assert response.json()["detail"] == "position_not_found"

    def test_auto_size_order_with_market_data(self, client, position_id):
        """Test auto-sizing order with market data."""
        response = client.post(f"/v1/positions/{position_id}/orders/auto-size/market")

        # This might fail if market data is not available
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["position_id"] == position_id
            assert "order_submitted" in data

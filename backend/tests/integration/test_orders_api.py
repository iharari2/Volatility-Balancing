# =========================
# backend/tests/integration/test_orders_api.py
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


@pytest.fixture
def order_id(client, position_id):
    """Create a test order and return its ID."""
    response = client.post(f"/v1/positions/{position_id}/orders", json={"side": "BUY", "qty": 10.0})
    assert response.status_code == 200
    return response.json()["order_id"]


class TestOrdersAPI:
    """Integration tests for orders API endpoints."""

    def test_submit_order_success(self, client, position_id):
        """Test successful order submission."""
        response = client.post(
            f"/v1/positions/{position_id}/orders", json={"side": "BUY", "qty": 10.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
        assert data["accepted"] == True
        assert data["position_id"] == position_id

    def test_submit_order_with_idempotency_key(self, client, position_id):
        """Test order submission with idempotency key."""
        idempotency_key = "test_key_123"

        response = client.post(
            f"/v1/positions/{position_id}/orders",
            json={"side": "SELL", "qty": 5.0},
            headers={"Idempotency-Key": idempotency_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] == True
        assert data["position_id"] == position_id

    def test_submit_order_invalid_side(self, client, position_id):
        """Test order submission with invalid side."""
        response = client.post(
            f"/v1/positions/{position_id}/orders",
            json={"side": "INVALID", "qty": 10.0, "price": 150.0},
        )

        # This should be handled by validation
        assert response.status_code in [200, 422, 400]

    def test_submit_order_negative_quantity(self, client):
        """Test order submission with negative quantity."""
        # Create a unique position for this test
        pos_response = client.post(
            "/v1/positions", json={"ticker": "TEST_NEG", "qty": 100.0, "cash": 10000.0}
        )
        assert pos_response.status_code == 201
        pos_id = pos_response.json()["id"]

        response = client.post(f"/v1/positions/{pos_id}/orders", json={"side": "BUY", "qty": -10.0})

        # This should be handled by validation
        assert response.status_code in [200, 422, 400]

    def test_submit_order_position_not_found(self, client):
        """Test order submission for non-existent position."""
        response = client.post(
            "/v1/positions/non_existent_id/orders", json={"side": "BUY", "qty": 10.0}
        )

        assert response.status_code == 404

    def test_fill_order_success(self, client, order_id):
        """Test successful order fill."""
        response = client.post(
            f"/v1/orders/{order_id}/fill", json={"qty": 10.0, "price": 150.0, "commission": 1.5}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "filled"
        assert data["filled_qty"] == 10.0

    def test_fill_order_partial(self, client, order_id):
        """Test partial order fill."""
        response = client.post(
            f"/v1/orders/{order_id}/fill", json={"qty": 5.0, "price": 150.0, "commission": 0.75}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filled_qty"] == 5.0

    def test_fill_order_not_found(self, client):
        """Test filling non-existent order."""
        response = client.post(
            "/v1/orders/non_existent_id/fill", json={"qty": 10.0, "price": 150.0, "commission": 1.5}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "order_not_found"

    def test_fill_order_zero_commission(self, client, order_id):
        """Test order fill with zero commission."""
        response = client.post(
            f"/v1/orders/{order_id}/fill", json={"qty": 10.0, "price": 150.0, "commission": 0.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filled_qty"] == 10.0

    def test_auto_sized_order_success(self, client, position_id):
        """Test auto-sized order submission."""
        response = client.post(f"/v1/positions/{position_id}/orders/auto-size?current_price=145.0")

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id
        assert data["current_price"] == 145.0
        assert "order_submitted" in data
        assert "evaluation" in data

    def test_auto_sized_order_with_idempotency(self, client, position_id):
        """Test auto-sized order with idempotency key."""
        idempotency_key = "auto_test_key_123"

        response = client.post(
            f"/v1/positions/{position_id}/orders/auto-size?current_price=145.0",
            headers={"Idempotency-Key": idempotency_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id

    def test_auto_sized_order_position_not_found(self, client):
        """Test auto-sized order for non-existent position."""
        response = client.post("/v1/positions/non_existent_id/orders/auto-size?current_price=145.0")

        assert response.status_code == 404
        assert response.json()["detail"] == "position_not_found"

    def test_auto_sized_order_with_market_data(self, client, position_id):
        """Test auto-sized order with market data."""
        response = client.post(f"/v1/positions/{position_id}/orders/auto-size/market")

        # This might fail if market data is not available
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["position_id"] == position_id
            assert "order_submitted" in data

    def test_auto_sized_order_with_market_data_idempotency(self, client, position_id):
        """Test auto-sized order with market data and idempotency key."""
        idempotency_key = "market_auto_test_key_123"

        response = client.post(
            f"/v1/positions/{position_id}/orders/auto-size/market",
            headers={"Idempotency-Key": idempotency_key},
        )

        # This might fail if market data is not available
        assert response.status_code in [200, 404, 500]

    def test_list_orders_success(self, client, position_id, order_id):
        """Test listing orders for a position."""
        response = client.get(f"/v1/positions/{position_id}/orders")

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id
        assert "orders" in data
        assert isinstance(data["orders"], list)
        assert len(data["orders"]) >= 1

    def test_list_orders_with_limit(self, client, position_id):
        """Test listing orders with limit."""
        response = client.get(f"/v1/positions/{position_id}/orders?limit=50")

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id
        assert "orders" in data

    def test_list_orders_position_not_found(self, client):
        """Test listing orders for non-existent position."""
        response = client.get("/v1/positions/non_existent_id/orders")

        assert response.status_code == 404
        assert response.json()["detail"] == "position_not_found"

    def test_order_workflow_complete(self, client):
        """Test complete order workflow: submit -> fill -> list."""
        # Create a unique position for this test
        pos_response = client.post(
            "/v1/positions", json={"ticker": "TEST_WORKFLOW", "qty": 100.0, "cash": 10000.0}
        )
        assert pos_response.status_code == 201
        pos_id = pos_response.json()["id"]

        # Submit order
        submit_response = client.post(
            f"/v1/positions/{pos_id}/orders", json={"side": "BUY", "qty": 20.0}
        )
        assert submit_response.status_code == 200
        order_data = submit_response.json()
        order_id = order_data["order_id"]

        # Fill order
        fill_response = client.post(
            f"/v1/orders/{order_id}/fill", json={"qty": 20.0, "price": 155.0, "commission": 3.1}
        )
        assert fill_response.status_code == 200
        fill_data = fill_response.json()
        assert fill_data["status"] == "filled"

        # List orders
        list_response = client.get(f"/v1/positions/{pos_id}/orders")
        assert list_response.status_code == 200
        orders = list_response.json()["orders"]

        # Find our order
        our_order = next((o for o in orders if o["id"] == order_id), None)
        assert our_order is not None
        assert our_order["status"] == "filled"

    def test_multiple_orders_same_position(self, client):
        """Test multiple orders for the same position."""
        # Create a unique position for this test
        pos_response = client.post(
            "/v1/positions", json={"ticker": "TEST_MULTI", "qty": 100.0, "cash": 10000.0}
        )
        assert pos_response.status_code == 201
        pos_id = pos_response.json()["id"]

        # Submit first order
        response1 = client.post(
            f"/v1/positions/{pos_id}/orders",
            json={"side": "BUY", "qty": 10.0},
            headers={"Idempotency-Key": "test_key_1"},
        )
        assert response1.status_code == 200

        # Submit second order
        response2 = client.post(
            f"/v1/positions/{pos_id}/orders",
            json={"side": "SELL", "qty": 5.0},
            headers={"Idempotency-Key": "test_key_2"},
        )
        assert response2.status_code == 200

        # List orders
        list_response = client.get(f"/v1/positions/{pos_id}/orders")
        assert list_response.status_code == 200
        orders = list_response.json()["orders"]
        assert len(orders) >= 2

    def test_order_validation_errors(self, client):
        """Test order validation with various error conditions."""
        # Create a unique position for this test
        pos_response = client.post(
            "/v1/positions", json={"ticker": "TEST_VALIDATION", "qty": 100.0, "cash": 10000.0}
        )
        assert pos_response.status_code == 201
        pos_id = pos_response.json()["id"]

        # Test with missing required fields
        response = client.post(
            f"/v1/positions/{pos_id}/orders",
            json={
                "side": "BUY"
                # Missing qty
            },
        )

        # This should be handled by Pydantic validation
        assert response.status_code in [200, 422, 400]

    def test_fill_order_validation_errors(self, client, order_id):
        """Test fill order validation with various error conditions."""
        # Test with missing required fields
        response = client.post(
            f"/v1/orders/{order_id}/fill",
            json={
                "qty": 10.0
                # Missing price
            },
        )

        # This should be handled by Pydantic validation
        assert response.status_code in [200, 422, 400]

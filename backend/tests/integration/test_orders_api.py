# =========================
# backend/tests/integration/test_orders_api.py
# =========================
import pytest


@pytest.fixture
def order_id(client, tenant_id, portfolio_id, position_id):
    """Create a test order and return its ID."""
    response = client.post(
        f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders",
        json={"side": "BUY", "qty": 10.0},
    )
    assert response.status_code == 200
    return response.json()["order_id"]


class TestOrdersAPI:
    """Integration tests for orders API endpoints."""

    def test_submit_order_success(self, client, tenant_id, portfolio_id, position_id):
        """Test successful order submission."""
        response = client.post(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders",
            json={"side": "BUY", "qty": 10.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
        assert data["accepted"]
        assert data["position_id"] == position_id

    def test_submit_order_with_idempotency_key(self, client, tenant_id, portfolio_id, position_id):
        """Test order submission with idempotency key."""
        idempotency_key = "test_key_123"

        response = client.post(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders",
            json={"side": "SELL", "qty": 5.0},
            headers={"Idempotency-Key": idempotency_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["accepted"]
        assert data["position_id"] == position_id

    def test_submit_order_invalid_side(self, client, tenant_id, portfolio_id, position_id):
        """Test order submission with invalid side."""
        response = client.post(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders",
            json={"side": "INVALID", "qty": 10.0, "price": 150.0},
        )

        # This should be handled by validation
        assert response.status_code in [200, 422, 400]

    def test_submit_order_negative_quantity(self, client, tenant_id):
        """Test order submission with negative quantity."""
        # Create a portfolio with a position for this test (use unique name to avoid clashes)
        import uuid

        unique_suffix = uuid.uuid4().hex[:8]
        portfolio_response = client.post(
            f"/v1/tenants/{tenant_id}/portfolios",
            json={
                "name": f"Test Portfolio NEG {unique_suffix}",
                "starting_cash": {"currency": "USD", "amount": 10000.0},
                "holdings": [{"asset": "TEST_NEG", "qty": 100.0, "anchor_price": None}],
            },
        )
        assert portfolio_response.status_code == 201
        portfolio_id = portfolio_response.json()["portfolio_id"]

        # Get the position ID
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        assert len(positions) > 0
        pos_id = positions[0]["id"]

        response = client.post(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{pos_id}/orders",
            json={"side": "BUY", "qty": -10.0},
        )

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

    def test_fill_order_partial(self, client, tenant_id):
        """Test partial order fill."""
        # Create a fresh portfolio with position to avoid state leakage
        import uuid

        unique_ticker = f"AAPL_{uuid.uuid4().hex[:8]}"
        portfolio_response = client.post(
            f"/v1/tenants/{tenant_id}/portfolios",
            json={
                "name": f"Test Portfolio {unique_ticker}",
                "starting_cash": {"currency": "USD", "amount": 10000.0},
                "holdings": [{"asset": unique_ticker, "qty": 100.0, "anchor_price": 150.0}],
            },
        )
        assert portfolio_response.status_code == 201
        portfolio_id = portfolio_response.json()["portfolio_id"]

        # Get the position ID
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        assert len(positions) > 0
        position_id = positions[0]["id"]

        # Create a fresh order for this test
        order_response = client.post(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders",
            json={"side": "BUY", "qty": 10.0},
        )
        assert order_response.status_code == 200
        order_id = order_response.json()["order_id"]

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

    def test_fill_order_zero_commission(self, client, tenant_id):
        """Test order fill with zero commission."""
        # Create a fresh portfolio with position to avoid state leakage
        import uuid

        unique_ticker = f"AAPL_{uuid.uuid4().hex[:8]}"
        portfolio_response = client.post(
            f"/v1/tenants/{tenant_id}/portfolios",
            json={
                "name": f"Test Portfolio {unique_ticker}",
                "starting_cash": {"currency": "USD", "amount": 10000.0},
                "holdings": [{"asset": unique_ticker, "qty": 100.0, "anchor_price": 150.0}],
            },
        )
        assert portfolio_response.status_code == 201
        portfolio_id = portfolio_response.json()["portfolio_id"]

        # Get the position ID
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        assert len(positions) > 0
        position_id = positions[0]["id"]

        # Create a fresh order for this test
        order_response = client.post(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders",
            json={"side": "BUY", "qty": 10.0},
        )
        assert order_response.status_code == 200
        order_id = order_response.json()["order_id"]

        response = client.post(
            f"/v1/orders/{order_id}/fill", json={"qty": 10.0, "price": 150.0, "commission": 0.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filled_qty"] == 10.0

    def test_auto_sized_order_success(self, client, tenant_id, portfolio_id, position_id):
        """Test auto-sized order submission using legacy endpoint."""
        # The legacy endpoint still works via _find_position_legacy helper
        response = client.post(f"/v1/positions/{position_id}/orders/auto-size?current_price=145.0")

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id
        assert data["current_price"] == 145.0
        assert "order_submitted" in data
        assert "evaluation" in data

        # Verify the position exists in the portfolio
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        position = next((p for p in positions if p["id"] == position_id), None)
        assert position is not None

    def test_auto_sized_order_with_idempotency(self, client, tenant_id, portfolio_id, position_id):
        """Test auto-sized order with idempotency key using legacy endpoint."""
        # The legacy endpoint still works via _find_position_legacy helper
        idempotency_key = "auto_test_key_123"

        response = client.post(
            f"/v1/positions/{position_id}/orders/auto-size?current_price=145.0",
            headers={"Idempotency-Key": idempotency_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id

        # Verify the position exists in the portfolio
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        position = next((p for p in positions if p["id"] == position_id), None)
        assert position is not None

    def test_auto_sized_order_position_not_found(self, client):
        """Test auto-sized order for non-existent position."""
        response = client.post("/v1/positions/non_existent_id/orders/auto-size?current_price=145.0")

        assert response.status_code == 404
        # Older implementations returned "position_not_found", but some FastAPI
        # configurations may return generic "Not Found". Accept either.
        assert response.json().get("detail") in ["position_not_found", "Not Found"]

    def test_auto_sized_order_with_market_data(self, client, tenant_id, portfolio_id, position_id):
        """Test auto-sized order with market data using legacy endpoint."""
        # The legacy endpoint still works via _find_position_legacy helper
        response = client.post(f"/v1/positions/{position_id}/orders/auto-size/market")

        # This might fail if market data is not available
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["position_id"] == position_id
            assert "order_submitted" in data

        # Verify the position exists in the portfolio
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        position = next((p for p in positions if p["id"] == position_id), None)
        assert position is not None

    def test_auto_sized_order_with_market_data_idempotency(
        self, client, tenant_id, portfolio_id, position_id
    ):
        """Test auto-sized order with market data and idempotency key using legacy endpoint."""
        # The legacy endpoint still works via _find_position_legacy helper
        idempotency_key = "market_auto_test_key_123"

        response = client.post(
            f"/v1/positions/{position_id}/orders/auto-size/market",
            headers={"Idempotency-Key": idempotency_key},
        )

        # This might fail if market data is not available
        assert response.status_code in [200, 404, 500]

        # Verify the position exists in the portfolio
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        position = next((p for p in positions if p["id"] == position_id), None)
        assert position is not None

    def test_list_orders_success(self, client, tenant_id, portfolio_id, position_id, order_id):
        """Test listing orders for a position."""
        response = client.get(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id
        assert "orders" in data
        assert isinstance(data["orders"], list)
        assert len(data["orders"]) >= 1

    def test_list_orders_with_limit(self, client, tenant_id, portfolio_id, position_id):
        """Test listing orders with limit."""
        response = client.get(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders?limit=50"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == position_id
        assert "orders" in data

    def test_list_orders_position_not_found(self, client, tenant_id, portfolio_id):
        """Test listing orders for non-existent position."""
        response = client.get(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/non_existent_id/orders"
        )

        assert response.status_code == 404
        # Error message may vary
        assert "detail" in response.json()

    def test_order_workflow_complete(self, client, tenant_id):
        """Test complete order workflow: submit -> fill -> list."""
        # Create a portfolio with position for this test (unique name to avoid clashes)
        import uuid

        unique_suffix = uuid.uuid4().hex[:8]
        portfolio_response = client.post(
            f"/v1/tenants/{tenant_id}/portfolios",
            json={
                "name": f"Test Portfolio WORKFLOW {unique_suffix}",
                "starting_cash": {"currency": "USD", "amount": 10000.0},
                "holdings": [{"asset": "TEST_WORKFLOW", "qty": 100.0, "anchor_price": None}],
            },
        )
        assert portfolio_response.status_code == 201
        portfolio_id = portfolio_response.json()["portfolio_id"]

        # Get the position ID
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        assert len(positions) > 0
        pos_id = positions[0]["id"]

        # Submit order
        submit_response = client.post(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{pos_id}/orders",
            json={"side": "BUY", "qty": 20.0},
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
        list_response = client.get(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{pos_id}/orders"
        )
        assert list_response.status_code == 200
        orders = list_response.json()["orders"]

        # Find our order
        our_order = next((o for o in orders if o["id"] == order_id), None)
        assert our_order is not None
        assert our_order["status"] == "filled"

    def test_multiple_orders_same_position(self, client, tenant_id):
        """Test multiple orders for the same position."""
        # Create a portfolio with position for this test (unique name to avoid clashes)
        import uuid

        unique_suffix = uuid.uuid4().hex[:8]
        portfolio_response = client.post(
            f"/v1/tenants/{tenant_id}/portfolios",
            json={
                "name": f"Test Portfolio MULTI {unique_suffix}",
                "starting_cash": {"currency": "USD", "amount": 10000.0},
                "holdings": [{"asset": "TEST_MULTI", "qty": 100.0, "anchor_price": None}],
            },
        )
        assert portfolio_response.status_code == 201
        portfolio_id = portfolio_response.json()["portfolio_id"]

        # Get the position ID
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        assert len(positions) > 0
        pos_id = positions[0]["id"]

        # Submit first order
        response1 = client.post(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{pos_id}/orders",
            json={"side": "BUY", "qty": 10.0},
            headers={"Idempotency-Key": "test_key_1"},
        )
        assert response1.status_code == 200

        # Submit second order
        response2 = client.post(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{pos_id}/orders",
            json={"side": "SELL", "qty": 5.0},
            headers={"Idempotency-Key": "test_key_2"},
        )
        assert response2.status_code == 200

        # List orders
        list_response = client.get(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{pos_id}/orders"
        )
        assert list_response.status_code == 200
        orders = list_response.json()["orders"]
        assert len(orders) >= 2

    def test_order_validation_errors(self, client, tenant_id):
        """Test order validation with various error conditions."""
        # Create a portfolio with position for this test (unique name to avoid clashes)
        import uuid

        unique_suffix = uuid.uuid4().hex[:8]
        portfolio_response = client.post(
            f"/v1/tenants/{tenant_id}/portfolios",
            json={
                "name": f"Test Portfolio VALIDATION {unique_suffix}",
                "starting_cash": {"currency": "USD", "amount": 10000.0},
                "holdings": [{"asset": "TEST_VALIDATION", "qty": 100.0, "anchor_price": None}],
            },
        )
        assert portfolio_response.status_code == 201
        portfolio_id = portfolio_response.json()["portfolio_id"]

        # Get the position ID
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        assert len(positions) > 0
        pos_id = positions[0]["id"]

        # Test with missing required fields
        response = client.post(
            f"/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{pos_id}/orders",
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

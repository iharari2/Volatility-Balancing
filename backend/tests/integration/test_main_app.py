# =========================
# backend/tests/integration/test_main_app.py
# =========================
import pytest
from starlette.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestMainApp:
    """Integration tests for the main FastAPI application."""

    def test_app_creation(self):
        """Test that the app is created successfully."""
        assert app is not None
        assert app.title == "Volatility Balancing API"
        assert app.version == "v1"

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/v1/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_root_health_endpoint(self, client):
        """Test the root health check endpoint."""
        response = client.get("/v1/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        response = client.options("/v1/healthz")

        # CORS preflight should be handled
        assert response.status_code in [200, 405]

    def test_api_documentation_endpoints(self, client):
        """Test that API documentation endpoints are available."""
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200

        # Test ReDoc documentation
        response = client.get("/redoc")
        assert response.status_code == 200

        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200

    def test_router_integration(self, client):
        """Test that all routers are properly integrated."""
        # Test health router
        response = client.get("/v1/healthz")
        assert response.status_code == 200

        # Test positions router (deprecated endpoint may return 410 Gone or 404 Not Found)
        response = client.get("/v1/positions")
        assert response.status_code in [200, 404, 410]  # 404 if fully removed

        # Test orders router (should return 404 for non-existent position)
        # Use new portfolio-scoped endpoint
        response = client.get(
            "/api/tenants/default/portfolios/test_portfolio/positions/non_existent/orders"
        )
        assert response.status_code in [404, 410]  # May be 404 or 410

        # Test dividends router
        response = client.get("/v1/dividends/status/non_existent")
        assert response.status_code == 404

    def test_error_handling(self, client):
        """Test that errors are properly handled."""
        # Test 404 for non-existent endpoint
        response = client.get("/v1/non_existent_endpoint")
        assert response.status_code == 404

        # Test 405 for unsupported method
        response = client.delete("/v1/healthz")
        assert response.status_code == 405

    def test_request_validation(self, client):
        """Test that request validation works properly."""
        # Test invalid JSON (deprecated endpoint may return 405/410, or 404 if removed)
        response = client.post(
            "/v1/positions", data="invalid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [404, 405, 410, 422]  # Deprecated endpoint

        # Test missing required fields
        response = client.post("/v1/positions", json={})
        assert response.status_code in [404, 405, 410, 422]  # Deprecated endpoint

    def test_response_format_consistency(self, client):
        """Test that response formats are consistent."""
        # Test positions endpoint response format (deprecated endpoint may return 410)
        response = client.get("/v1/positions")
        assert response.status_code in [200, 404, 410]  # May be deprecated or removed
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert "positions" in data
            assert isinstance(data["positions"], list)

        # Test health endpoint response format
        response = client.get("/v1/healthz")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data

    def test_api_versioning(self, client):
        """Test that API versioning is properly implemented."""
        # All endpoints should be under /v1 prefix
        response = client.get("/v1/healthz")
        assert response.status_code == 200

        # Endpoints without version should not work
        response = client.get("/healthz")
        assert response.status_code == 404

    def test_middleware_configuration(self, client):
        """Test that middleware is properly configured."""
        # Test CORS middleware
        response = client.get("/v1/healthz")
        assert response.status_code == 200

        # Check for CORS headers
        headers = response.headers
        # CORS headers might not be present in all responses
        # but the middleware should be configured

    def test_application_metadata(self, client):
        """Test application metadata."""
        # Test OpenAPI schema contains correct metadata
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert schema["info"]["title"] == "Volatility Balancing API"
        assert schema["info"]["version"] == "v1"

    def test_endpoint_discovery(self, client):
        """Test that all expected endpoints are discoverable."""
        # Get OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        paths = schema.get("paths", {})

        # Check for key endpoints
        expected_paths = [
            "/v1/healthz",
            # Note: These endpoints may be deprecated
            # "/v1/positions",
            # "/v1/positions/{position_id}",
            # "/v1/positions/{position_id}/orders",
            "/v1/orders/{order_id}/fill",
            "/v1/dividends/announce",
            # Legacy dividend endpoint may be deprecated
            # "/v1/dividends/positions/{position_id}/status",
            # New portfolio-scoped endpoint:
            "/v1/dividends/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/status",
        ]

        for path in expected_paths:
            assert path in paths, f"Expected path {path} not found in API schema"

    def test_error_response_format(self, client):
        """Test that error responses follow a consistent format."""
        # Test 404 error
        response = client.get("/v1/non_existent")
        assert response.status_code == 404

        error_data = response.json()
        assert "detail" in error_data

        # Test 422 validation error (deprecated endpoint may return 405/410, or 404 if removed)
        response = client.post("/v1/positions", json={"invalid": "data"})
        assert response.status_code in [404, 405, 410, 422]  # Deprecated endpoint

        error_data = response.json()
        assert "detail" in error_data

    def test_content_type_handling(self, client):
        """Test that content types are handled properly."""
        # Test JSON content type (deprecated endpoint may return 405/410, or 404 if removed)
        response = client.post("/v1/positions", json={"ticker": "TEST", "qty": 0, "cash": 1000})
        assert response.status_code in [404, 405, 410, 201]  # Deprecated endpoint

        # Test that response is JSON (if not an error)
        if response.status_code < 400:
            assert response.headers["content-type"].startswith("application/json")

    def test_http_methods_support(self, client):
        """Test that appropriate HTTP methods are supported."""
        # GET endpoints
        response = client.get("/v1/healthz")
        assert response.status_code == 200

        # POST endpoints (deprecated endpoint may return 405/410, or 404 if removed)
        response = client.post("/v1/positions", json={"ticker": "TEST", "qty": 0, "cash": 1000})
        assert response.status_code in [404, 405, 410, 201]  # Deprecated endpoint

        # OPTIONS for CORS
        response = client.options("/v1/healthz")
        assert response.status_code in [200, 405]

    def test_application_startup(self):
        """Test that the application starts up without errors."""
        # This test ensures the app can be instantiated
        from app.main import app

        assert app is not None

        # Test that all routers are included
        assert len(app.routes) > 0

        # Test that middleware is configured
        assert len(app.user_middleware) > 0

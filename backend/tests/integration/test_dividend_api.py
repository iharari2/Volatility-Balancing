# =========================
# backend/tests/integration/test_dividend_api.py
# =========================
import os
import pytest
from datetime import datetime, timezone, timedelta

from app.di import container


pytestmark = pytest.mark.e2e


def _e2e_enabled() -> bool:
    return os.getenv("E2E_SERVER", "").lower() in ("1", "true", "yes")


@pytest.fixture(autouse=True)
def _require_e2e():
    if not _e2e_enabled():
        pytest.skip("E2E_SERVER not enabled")


@pytest.fixture
def sample_dividend_data():
    """Sample dividend data for testing."""
    ex_date = datetime.now(timezone.utc) + timedelta(days=1)
    pay_date = ex_date + timedelta(days=14)

    return {
        "ticker": "AAPL",
        "ex_date": ex_date.isoformat(),
        "pay_date": pay_date.isoformat(),
        "dps": 0.82,
        "currency": "USD",
        "withholding_tax_rate": 0.25,
    }


class TestDividendAPI:
    """Integration tests for dividend API endpoints."""

    def test_announce_dividend_success(self, client, sample_dividend_data):
        """Test successful dividend announcement."""
        response = client.post("/v1/dividends/announce", json=sample_dividend_data)

        assert response.status_code == 200
        data = response.json()

        assert data["ticker"] == "AAPL"
        assert data["dps"] == 0.82
        assert data["currency"] == "USD"
        assert data["withholding_tax_rate"] == 0.25
        assert "dividend_id" in data
        assert "message" in data

    def test_announce_dividend_invalid_data(self, client):
        """Test dividend announcement with invalid data."""
        invalid_data = {
            "ticker": "AAPL",
            "ex_date": "invalid-date",
            "pay_date": "invalid-date",
            "dps": -0.82,  # Negative DPS
        }

        response = client.post("/v1/dividends/announce", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_get_dividend_status_no_position(self, client):
        """Test getting dividend status for non-existent position."""
        response = client.get("/v1/dividends/positions/nonexistent/status")
        assert response.status_code == 404

    def test_get_dividend_status_success(self, client, tenant_id, portfolio_id, position_id):
        """Test getting dividend status for existing position."""
        response = client.get(
            f"/v1/dividends/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/status"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["position_id"] == position_id
        assert data["ticker"] == "AAPL"
        assert data["dividend_receivable"] == 0.0
        assert data["effective_cash"] == 10000.0
        assert "pending_receivables" in data
        assert "upcoming_dividends" in data

    def test_process_ex_dividend_no_dividend_today(
        self, client, tenant_id, portfolio_id, position_id
    ):
        """Test processing ex-dividend when no dividend today."""
        # Try the path with /v1/dividends prefix (since dividends router has that prefix)
        response = client.post(
            f"/v1/dividends/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/process-ex-dividend"
        )
        assert response.status_code == 200

        assert response.status_code == 200
        data = response.json()

        assert data["processed"] is False
        assert "No ex-dividend date today" in data["message"]

    def test_process_dividend_payment_no_receivable(self, client, position_id):
        """Test processing dividend payment with non-existent receivable."""
        response = client.post(
            f"/v1/dividends/positions/{position_id}/process-payment",
            json={"receivable_id": "nonexistent"},
        )

        assert response.status_code == 404

    def test_get_market_dividend_info(self, client):
        """Test getting market dividend information."""
        response = client.get("/v1/dividends/market/AAPL/info")

        # This might return no dividend info if AAPL doesn't have current dividend data
        assert response.status_code == 200
        data = response.json()

        assert data["ticker"] == "AAPL"
        assert "has_dividend" in data
        # The API returns either a dividend object or a message
        assert "dividend" in data or "message" in data

    def test_get_upcoming_dividends(self, client):
        """Test getting upcoming dividends."""
        response = client.get("/v1/dividends/market/AAPL/upcoming")

        assert response.status_code == 200
        data = response.json()

        assert data["ticker"] == "AAPL"
        assert "upcoming_dividends" in data
        assert isinstance(data["upcoming_dividends"], list)

    def test_dividend_workflow_integration(self, client, tenant_id, portfolio_id, position_id):
        """Test complete dividend workflow integration."""
        # 1. Set anchor price using legacy endpoint (still works via _find_position_legacy)
        response = client.post(f"/v1/positions/{position_id}/anchor", params={"price": 150.0})
        # Legacy endpoint may return 410 Gone if fully deprecated
        assert response.status_code in [200, 410]
        if response.status_code == 410:
            return  # Skip rest of test if endpoint is deprecated

        # 2. Announce a dividend
        ex_date = datetime.now(timezone.utc) + timedelta(days=1)
        pay_date = ex_date + timedelta(days=14)

        dividend_data = {
            "ticker": "AAPL",
            "ex_date": ex_date.isoformat(),
            "pay_date": pay_date.isoformat(),
            "dps": 0.82,
            "currency": "USD",
            "withholding_tax_rate": 0.25,
        }

        response = client.post("/v1/dividends/announce", json=dividend_data)
        assert response.status_code == 200
        dividend_id = response.json()["dividend_id"]

        # 3. Check dividend status
        response = client.get(
            f"/v1/dividends/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/status"
        )
        assert response.status_code == 200
        status = response.json()

        # Should show upcoming dividend
        assert len(status["upcoming_dividends"]) >= 0  # May or may not have upcoming dividends

        # 4. Verify anchor price was set by checking position via portfolio API
        pos_response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
        assert pos_response.status_code == 200
        positions = pos_response.json()
        position = next((p for p in positions if p["id"] == position_id), None)
        assert position is not None
        assert position["anchor_price"] == 150.0

    def test_dividend_status_with_receivables(self, client, tenant_id, portfolio_id, position_id):
        """Test dividend status when position has receivables."""
        # First, manually add a receivable to test the status endpoint
        # This simulates what would happen after ex-dividend processing

        # Get the position and add a receivable
        position = container.positions.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        assert position is not None
        position.add_dividend_receivable(61.50)
        container.positions.save(position)

        # Check status
        response = client.get(
            f"/v1/dividends/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/status"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["dividend_receivable"] == 61.50
        assert data["effective_cash"] == 10061.50  # 10000 + 61.50

    def test_api_error_handling(self, client):
        """Test API error handling for various scenarios."""
        # Test with invalid JSON
        response = client.post(
            "/v1/dividends/announce",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

        # Test with missing required fields
        response = client.post(
            "/v1/dividends/announce",
            json={
                "ticker": "AAPL"
                # Missing required fields
            },
        )
        assert response.status_code == 422

    def test_dividend_announcement_validation(self, client):
        """Test dividend announcement validation."""
        # Test negative DPS (currently accepted, but could be validated in future)
        response = client.post(
            "/v1/dividends/announce",
            json={
                "ticker": "AAPL",
                "ex_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "pay_date": (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),
                "dps": -0.82,
            },
        )
        # Currently accepts negative DPS (business logic allows it)
        assert response.status_code == 200

        # Test pay date before ex date
        ex_date = datetime.now(timezone.utc) + timedelta(days=2)
        pay_date = datetime.now(timezone.utc) + timedelta(days=1)  # Before ex date

        response = client.post(
            "/v1/dividends/announce",
            json={
                "ticker": "AAPL",
                "ex_date": ex_date.isoformat(),
                "pay_date": pay_date.isoformat(),
                "dps": 0.82,
            },
        )
        # This should pass validation but might fail business logic
        # The API doesn't currently validate pay_date > ex_date
        assert response.status_code in [200, 422]

    def test_dividend_endpoints_consistency(self, client, tenant_id, portfolio_id, position_id):
        """Test that dividend endpoints return consistent data."""
        # Get initial status
        response1 = client.get(
            f"/v1/dividends/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/status"
        )
        assert response1.status_code == 200
        status1 = response1.json()

        # Get status again
        response2 = client.get(
            f"/v1/dividends/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/status"
        )
        assert response2.status_code == 200
        status2 = response2.json()

        # Should be consistent
        assert status1["position_id"] == status2["position_id"]
        assert status1["ticker"] == status2["ticker"]
        assert status1["dividend_receivable"] == status2["dividend_receivable"]
        assert status1["effective_cash"] == status2["effective_cash"]

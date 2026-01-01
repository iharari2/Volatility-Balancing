# =========================
# backend/tests/unit/application/test_process_dividend_uc.py
# =========================
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

from domain.entities.dividend import Dividend, DividendReceivable
from domain.entities.position import Position
from application.use_cases.process_dividend_uc import ProcessDividendUC


class TestProcessDividendUC:
    """Test cases for ProcessDividendUC."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "dividend_repo": Mock(),
            "dividend_receivable_repo": Mock(),
            "dividend_market_data_repo": Mock(),
            "positions_repo": Mock(),
            "events_repo": Mock(),
            "clock": Mock(),
        }

    @pytest.fixture
    def dividend_uc(self, mock_repos):
        """Create ProcessDividendUC with mock dependencies."""

        return ProcessDividendUC(
            dividend_repo=mock_repos["dividend_repo"],
            dividend_receivable_repo=mock_repos["dividend_receivable_repo"],
            dividend_market_data_repo=mock_repos["dividend_market_data_repo"],
            positions_repo=mock_repos["positions_repo"],
            events_repo=mock_repos["events_repo"],
            clock=mock_repos["clock"],
        )

    @pytest.fixture
    def sample_dividend(self):
        """Create a sample dividend."""
        return Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=datetime(2024, 3, 15, tzinfo=timezone.utc),
            pay_date=datetime(2024, 3, 29, tzinfo=timezone.utc),
            dps=Decimal("0.82"),
            currency="USD",
            withholding_tax_rate=0.25,
        )

    @pytest.fixture
    def sample_position(self):
        """Create a sample position."""
        return Position(
            id="pos123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            anchor_price=150.0,
            dividend_receivable=0.0,
            withholding_tax_rate=0.25,
        )

    def test_announce_dividend(self, dividend_uc, mock_repos):
        """Test dividend announcement."""
        # Arrange
        ex_date = datetime(2024, 3, 15, tzinfo=timezone.utc)
        pay_date = datetime(2024, 3, 29, tzinfo=timezone.utc)
        mock_repos["clock"].now.return_value = datetime(2024, 3, 1, tzinfo=timezone.utc)

        # Mock the repository to return the created dividend
        created_dividend = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=ex_date,
            pay_date=pay_date,
            dps=Decimal("0.82"),
            currency="USD",
            withholding_tax_rate=0.25,
        )
        mock_repos["dividend_repo"].create_dividend.return_value = created_dividend

        # Act
        result = dividend_uc.announce_dividend(
            ticker="AAPL",
            ex_date=ex_date,
            pay_date=pay_date,
            dps=0.82,
            currency="USD",
            withholding_tax_rate=0.25,
        )

        # Assert
        assert result == created_dividend
        mock_repos["dividend_repo"].create_dividend.assert_called_once()
        mock_repos["events_repo"].append.assert_called_once()

        # Verify event creation
        event_call = mock_repos["events_repo"].append.call_args[0][0]
        assert event_call.type == "ex_div_announced"
        assert event_call.position_id == "system"
        assert "AAPL" in event_call.message

    def test_process_ex_dividend_date_success(
        self, dividend_uc, mock_repos, sample_dividend, sample_position
    ):
        """Test successful ex-dividend date processing."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "pos123"
        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos[
            "dividend_market_data_repo"
        ].check_ex_dividend_today.return_value = sample_dividend
        mock_repos["clock"].now.return_value = datetime(2024, 3, 15, tzinfo=timezone.utc)

        # Mock receivable creation
        created_receivable = DividendReceivable(
            id="rec_pos123_div_AAPL_20240315",
            position_id=position_id,
            dividend_id=sample_dividend.id,
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50"),
        )
        mock_repos["dividend_receivable_repo"].create_receivable.return_value = created_receivable

        # Act
        result = dividend_uc.process_ex_dividend_date(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

        # Assert
        assert result is not None
        assert result["dividend"] == sample_dividend
        assert result["receivable"] == created_receivable
        assert result["old_anchor"] == 150.0
        assert result["new_anchor"] == 149.18  # 150.0 - 0.82

        # Verify position was updated
        assert sample_position.anchor_price == 149.18
        assert sample_position.dividend_receivable == 61.50

        # Verify repositories were called
        mock_repos["positions_repo"].get.assert_called_once_with(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        mock_repos["dividend_market_data_repo"].check_ex_dividend_today.assert_called_once_with(
            "AAPL"
        )
        mock_repos["dividend_receivable_repo"].create_receivable.assert_called_once()
        mock_repos["positions_repo"].save.assert_called_once_with(sample_position)

        # Verify events were created
        assert mock_repos["events_repo"].append.call_count == 2

    def test_process_ex_dividend_date_no_position(self, dividend_uc, mock_repos):
        """Test ex-dividend processing when position doesn't exist."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "nonexistent"
        mock_repos["positions_repo"].get.return_value = None

        # Act
        result = dividend_uc.process_ex_dividend_date(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

        # Assert
        assert result is None
        mock_repos["positions_repo"].get.assert_called_once_with(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

    def test_process_ex_dividend_date_no_dividend_today(
        self, dividend_uc, mock_repos, sample_position
    ):
        """Test ex-dividend processing when no dividend today."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "pos123"
        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["dividend_market_data_repo"].check_ex_dividend_today.return_value = None

        # Act
        result = dividend_uc.process_ex_dividend_date(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

        # Assert
        assert result is None
        mock_repos["positions_repo"].get.assert_called_once_with(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        mock_repos["dividend_market_data_repo"].check_ex_dividend_today.assert_called_once_with(
            "AAPL"
        )

    def test_process_dividend_payment_success(self, dividend_uc, mock_repos, sample_position):
        """Test successful dividend payment processing."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "pos123"
        receivable_id = "rec123"

        receivable = DividendReceivable(
            id=receivable_id,
            position_id=position_id,
            dividend_id="div123",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50"),
        )

        mock_repos["dividend_receivable_repo"].get_receivable.return_value = receivable
        sample_position.cash = 10000.0
        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["clock"].now.return_value = datetime(2024, 3, 29, tzinfo=timezone.utc)

        # Act
        result = dividend_uc.process_dividend_payment(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            receivable_id=receivable_id,
        )

        # Assert
        assert result is not None
        assert result["receivable"] == receivable
        assert result["amount_received"] == 61.50
        # Cash is now stored in Position.cash (cash lives in PositionCell)
        assert result["new_cash_balance"] == sample_position.cash  # Updated cash balance

        # Verify receivable was marked as paid
        assert receivable.status == "paid"
        assert receivable.paid_at is not None

        # Verify position was updated (cash lives in Position entity)
        assert sample_position.dividend_receivable == 0.0
        assert sample_position.total_dividends_received == 61.50

        # Verify position cash was updated (cash lives in PositionCell)
        assert sample_position.cash == 10061.50

        # Verify repositories were called
        mock_repos["dividend_receivable_repo"].get_receivable.assert_called_once_with(receivable_id)
        mock_repos["positions_repo"].get.assert_called_once_with(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        # Note: Cash is now stored in Position.cash, not PortfolioCash
        mock_repos["dividend_receivable_repo"].mark_receivable_paid.assert_called_once_with(
            receivable_id
        )
        mock_repos["positions_repo"].save.assert_called_once_with(sample_position)

        # Verify event was created
        mock_repos["events_repo"].append.assert_called_once()

    def test_process_dividend_payment_receivable_not_found(self, dividend_uc, mock_repos):
        """Test dividend payment when receivable doesn't exist."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "pos123"
        receivable_id = "nonexistent"
        mock_repos["dividend_receivable_repo"].get_receivable.return_value = None

        # Act
        result = dividend_uc.process_dividend_payment(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            receivable_id=receivable_id,
        )

        # Assert
        assert result is None
        mock_repos["dividend_receivable_repo"].get_receivable.assert_called_once_with(receivable_id)

    def test_process_dividend_payment_wrong_position(self, dividend_uc, mock_repos):
        """Test dividend payment when receivable belongs to different position."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "pos123"
        receivable_id = "rec123"

        receivable = DividendReceivable(
            id=receivable_id,
            position_id="different_position",
            dividend_id="div123",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50"),
        )

        mock_repos["dividend_receivable_repo"].get_receivable.return_value = receivable

        # Act
        result = dividend_uc.process_dividend_payment(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            receivable_id=receivable_id,
        )

        # Assert
        assert result is None
        mock_repos["dividend_receivable_repo"].get_receivable.assert_called_once_with(receivable_id)

    def test_get_dividend_status(self, dividend_uc, mock_repos, sample_position):
        """Test getting dividend status for a position."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "pos123"
        mock_repos["positions_repo"].get.return_value = sample_position

        # Mock pending receivables
        pending_receivables = [
            DividendReceivable(
                id="rec1",
                position_id=position_id,
                dividend_id="div1",
                shares_at_record=100.0,
                gross_amount=Decimal("82.00"),
                net_amount=Decimal("61.50"),
                withholding_tax=Decimal("20.50"),
            )
        ]
        mock_repos[
            "dividend_receivable_repo"
        ].get_pending_receivables.return_value = pending_receivables

        # Mock upcoming dividends
        upcoming_dividends = [
            Dividend(
                id="div2",
                ticker="AAPL",
                ex_date=datetime(2024, 6, 15, tzinfo=timezone.utc),
                pay_date=datetime(2024, 6, 29, tzinfo=timezone.utc),
                dps=Decimal("0.85"),
            )
        ]
        mock_repos[
            "dividend_market_data_repo"
        ].get_upcoming_dividends.return_value = upcoming_dividends
        sample_position.cash = 10000.0
        mock_repos["positions_repo"].get.return_value = sample_position

        # Act
        result = dividend_uc.get_dividend_status(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

        # Assert
        assert result["position_id"] == position_id
        assert result["ticker"] == sample_position.ticker
        assert result["dividend_receivable"] == sample_position.dividend_receivable
        assert result["effective_cash"] == sample_position.get_effective_cash()
        assert len(result["pending_receivables"]) == 1
        assert len(result["upcoming_dividends"]) == 1

        # Verify repository calls
        mock_repos["positions_repo"].get.assert_called_once_with(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        # Note: Cash is now stored in Position.cash, not PortfolioCash
        mock_repos["dividend_receivable_repo"].get_pending_receivables.assert_called_once_with(
            position_id
        )
        mock_repos["dividend_market_data_repo"].get_upcoming_dividends.assert_called_once_with(
            "AAPL"
        )

    def test_get_dividend_status_no_position(self, dividend_uc, mock_repos):
        """Test getting dividend status when position doesn't exist."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "nonexistent"
        mock_repos["positions_repo"].get.return_value = None

        # Act
        result = dividend_uc.get_dividend_status(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

        # Assert
        assert result == {}
        mock_repos["positions_repo"].get.assert_called_once_with(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

    def test_create_event(self, dividend_uc, mock_repos):
        """Test event creation helper method."""
        # Arrange
        mock_repos["clock"].now.return_value = datetime(
            2024, 3, 15, 12, 30, 45, 123456, tzinfo=timezone.utc
        )

        # Act
        event = dividend_uc._create_event(
            position_id="pos123",
            event_type="test_event",
            inputs={"key": "value"},
            outputs={"result": "success"},
            message="Test event",
        )

        # Assert
        assert event.position_id == "pos123"
        assert event.type == "test_event"
        assert event.inputs == {"key": "value"}
        assert event.outputs == {"result": "success"}
        assert event.message == "Test event"
        assert event.ts == datetime(2024, 3, 15, 12, 30, 45, 123456, tzinfo=timezone.utc)

        # Verify event was created with proper ID format
        assert event.id.startswith("evt_test_event_20240315_123045_")

        # Verify event was saved
        mock_repos["events_repo"].append.assert_called_once_with(event)

    def test_create_event_system_position(self, dividend_uc, mock_repos):
        """Test event creation with system position."""
        # Arrange
        mock_repos["clock"].now.return_value = datetime(
            2024, 3, 15, 12, 30, 45, 123456, tzinfo=timezone.utc
        )

        # Act
        event = dividend_uc._create_event(
            position_id=None,
            event_type="system_event",
            inputs={"key": "value"},
            outputs={"result": "success"},
            message="System event",
        )

        # Assert
        assert event.position_id == "system"
        assert event.type == "system_event"

    def test_process_dividend_payment_increments_aggregate(
        self, dividend_uc, mock_repos, sample_position
    ):
        """Test that total_dividends_received is incremented on dividend payment."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "pos123"
        receivable_id = "rec123"

        receivable = DividendReceivable(
            id=receivable_id,
            position_id=position_id,
            dividend_id="div123",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50"),
        )

        # Set initial aggregate to 0.0
        sample_position.total_dividends_received = 0.0

        mock_repos["dividend_receivable_repo"].get_receivable.return_value = receivable
        sample_position.cash = 10000.0
        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["clock"].now.return_value = datetime(2024, 3, 29, tzinfo=timezone.utc)

        # Act
        result = dividend_uc.process_dividend_payment(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            receivable_id=receivable_id,
        )

        # Assert
        assert result is not None
        assert sample_position.total_dividends_received == 61.50  # Net amount added

    def test_process_dividend_payment_aggregates_multiple_payments(
        self, dividend_uc, mock_repos, sample_position
    ):
        """Test that total_dividends_received aggregates across multiple payments."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "pos123"
        sample_position.total_dividends_received = 0.0

        # Cash is now stored in Position.cash, not PortfolioCash
        # Process first dividend payment
        receivable1 = DividendReceivable(
            id="rec1",
            position_id=position_id,
            dividend_id="div1",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50"),
        )

        mock_repos["dividend_receivable_repo"].get_receivable.return_value = receivable1
        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["clock"].now.return_value = datetime(2024, 3, 29, tzinfo=timezone.utc)

        # Act - First payment
        dividend_uc.process_dividend_payment(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            receivable_id="rec1",
        )

        # Verify first payment
        assert sample_position.total_dividends_received == 61.50

        # Process second dividend payment
        receivable2 = DividendReceivable(
            id="rec2",
            position_id=position_id,
            dividend_id="div2",
            shares_at_record=100.0,
            gross_amount=Decimal("100.00"),
            net_amount=Decimal("75.00"),
            withholding_tax=Decimal("25.00"),
        )

        mock_repos["dividend_receivable_repo"].get_receivable.return_value = receivable2
        mock_repos["positions_repo"].get.return_value = sample_position

        # Act - Second payment
        dividend_uc.process_dividend_payment(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            receivable_id="rec2",
        )

        # Assert - Should aggregate both payments
        assert sample_position.total_dividends_received == 136.50  # 61.50 + 75.00

    def test_process_dividend_payment_aggregate_starts_at_zero(
        self, dividend_uc, mock_repos, sample_position
    ):
        """Test that new positions start with total_dividends_received = 0.0."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "pos123"
        receivable_id = "rec123"

        # Ensure position starts with 0.0
        sample_position.total_dividends_received = 0.0

        receivable = DividendReceivable(
            id=receivable_id,
            position_id=position_id,
            dividend_id="div123",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50"),
        )

        # Cash is now stored in Position.cash, not PortfolioCash
        mock_repos["dividend_receivable_repo"].get_receivable.return_value = receivable
        sample_position.cash = 10000.0
        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["clock"].now.return_value = datetime(2024, 3, 29, tzinfo=timezone.utc)

        # Act
        dividend_uc.process_dividend_payment(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            receivable_id=receivable_id,
        )

        # Assert
        assert sample_position.total_dividends_received == 61.50

    def test_dividend_aggregate_independent_from_commission(
        self, dividend_uc, mock_repos, sample_position
    ):
        """Test that dividend and commission aggregates are independent."""
        # Arrange
        tenant_id = "default"
        portfolio_id = "test_portfolio"
        position_id = "pos123"
        receivable_id = "rec123"

        # Set initial values
        sample_position.total_commission_paid = 10.0
        sample_position.total_dividends_received = 50.0

        receivable = DividendReceivable(
            id=receivable_id,
            position_id=position_id,
            dividend_id="div123",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50"),
        )

        # Cash is now stored in Position.cash, not PortfolioCash
        mock_repos["dividend_receivable_repo"].get_receivable.return_value = receivable
        sample_position.cash = 10000.0
        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["clock"].now.return_value = datetime(2024, 3, 29, tzinfo=timezone.utc)

        # Act
        dividend_uc.process_dividend_payment(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            receivable_id=receivable_id,
        )

        # Assert - Commission should remain unchanged
        assert sample_position.total_commission_paid == 10.0
        assert sample_position.total_dividends_received == 111.50  # 50.0 + 61.50

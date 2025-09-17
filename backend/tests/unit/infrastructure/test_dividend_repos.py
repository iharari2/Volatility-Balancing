# =========================
# backend/tests/unit/infrastructure/test_dividend_repos.py
# =========================
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from domain.entities.dividend import Dividend, DividendReceivable
from infrastructure.persistence.memory.dividend_repo import InMemoryDividendRepo, InMemoryDividendReceivableRepo


class TestInMemoryDividendRepo:
    """Test cases for InMemoryDividendRepo."""

    @pytest.fixture
    def repo(self):
        """Create repository instance."""
        return InMemoryDividendRepo()

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
            withholding_tax_rate=0.25
        )

    def test_create_dividend(self, repo, sample_dividend):
        """Test creating a dividend."""
        result = repo.create_dividend(sample_dividend)
        
        assert result == sample_dividend
        assert repo.get_dividend(sample_dividend.id) == sample_dividend

    def test_get_dividend_existing(self, repo, sample_dividend):
        """Test getting an existing dividend."""
        repo.create_dividend(sample_dividend)
        
        result = repo.get_dividend(sample_dividend.id)
        assert result == sample_dividend

    def test_get_dividend_nonexistent(self, repo):
        """Test getting a non-existent dividend."""
        result = repo.get_dividend("nonexistent")
        assert result is None

    def test_get_dividends_by_ticker(self, repo):
        """Test getting dividends by ticker."""
        # Create dividends for different tickers
        aapl_dividend = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=datetime(2024, 3, 15, tzinfo=timezone.utc),
            pay_date=datetime(2024, 3, 29, tzinfo=timezone.utc),
            dps=Decimal("0.82")
        )
        
        msft_dividend = Dividend(
            id="div_MSFT_20240320",
            ticker="MSFT",
            ex_date=datetime(2024, 3, 20, tzinfo=timezone.utc),
            pay_date=datetime(2024, 4, 3, tzinfo=timezone.utc),
            dps=Decimal("0.75")
        )
        
        repo.create_dividend(aapl_dividend)
        repo.create_dividend(msft_dividend)
        
        # Test getting AAPL dividends
        aapl_dividends = repo.get_dividends_by_ticker("AAPL")
        assert len(aapl_dividends) == 1
        assert aapl_dividends[0] == aapl_dividend
        
        # Test getting MSFT dividends
        msft_dividends = repo.get_dividends_by_ticker("MSFT")
        assert len(msft_dividends) == 1
        assert msft_dividends[0] == msft_dividend

    def test_get_upcoming_dividends(self, repo):
        """Test getting upcoming dividends from a date."""
        base_date = datetime(2024, 3, 1, tzinfo=timezone.utc)
        
        # Create dividends with different dates
        past_dividend = Dividend(
            id="div_AAPL_20240215",
            ticker="AAPL",
            ex_date=datetime(2024, 2, 15, tzinfo=timezone.utc),
            pay_date=datetime(2024, 2, 29, tzinfo=timezone.utc),
            dps=Decimal("0.80")
        )
        
        future_dividend = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=datetime(2024, 3, 15, tzinfo=timezone.utc),
            pay_date=datetime(2024, 3, 29, tzinfo=timezone.utc),
            dps=Decimal("0.82")
        )
        
        repo.create_dividend(past_dividend)
        repo.create_dividend(future_dividend)
        
        # Test getting upcoming dividends
        upcoming = repo.get_upcoming_dividends("AAPL", base_date)
        assert len(upcoming) == 1
        assert upcoming[0] == future_dividend

    def test_get_dividend_by_ex_date(self, repo):
        """Test getting dividend by ex-date."""
        ex_date = datetime(2024, 3, 15, tzinfo=timezone.utc)
        
        dividend = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=ex_date,
            pay_date=datetime(2024, 3, 29, tzinfo=timezone.utc),
            dps=Decimal("0.82")
        )
        
        repo.create_dividend(dividend)
        
        # Test getting by exact ex-date
        result = repo.get_dividend_by_ex_date("AAPL", ex_date)
        assert result == dividend
        
        # Test getting by different ex-date
        different_date = datetime(2024, 3, 16, tzinfo=timezone.utc)
        result = repo.get_dividend_by_ex_date("AAPL", different_date)
        assert result is None


class TestInMemoryDividendReceivableRepo:
    """Test cases for InMemoryDividendReceivableRepo."""

    @pytest.fixture
    def repo(self):
        """Create repository instance."""
        return InMemoryDividendReceivableRepo()

    @pytest.fixture
    def sample_receivable(self):
        """Create a sample receivable."""
        return DividendReceivable(
            id="rec_pos123_div456",
            position_id="pos123",
            dividend_id="div456",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50")
        )

    def test_create_receivable(self, repo, sample_receivable):
        """Test creating a receivable."""
        result = repo.create_receivable(sample_receivable)
        
        assert result == sample_receivable
        assert repo.get_receivable(sample_receivable.id) == sample_receivable

    def test_get_receivable_existing(self, repo, sample_receivable):
        """Test getting an existing receivable."""
        repo.create_receivable(sample_receivable)
        
        result = repo.get_receivable(sample_receivable.id)
        assert result == sample_receivable

    def test_get_receivable_nonexistent(self, repo):
        """Test getting a non-existent receivable."""
        result = repo.get_receivable("nonexistent")
        assert result is None

    def test_get_receivables_by_position(self, repo):
        """Test getting receivables by position."""
        # Create receivables for different positions
        pos1_receivable = DividendReceivable(
            id="rec_pos1_div1",
            position_id="pos1",
            dividend_id="div1",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50")
        )
        
        pos2_receivable = DividendReceivable(
            id="rec_pos2_div2",
            position_id="pos2",
            dividend_id="div2",
            shares_at_record=50.0,
            gross_amount=Decimal("41.00"),
            net_amount=Decimal("30.75"),
            withholding_tax=Decimal("10.25")
        )
        
        repo.create_receivable(pos1_receivable)
        repo.create_receivable(pos2_receivable)
        
        # Test getting pos1 receivables
        pos1_receivables = repo.get_receivables_by_position("pos1")
        assert len(pos1_receivables) == 1
        assert pos1_receivables[0] == pos1_receivable
        
        # Test getting pos2 receivables
        pos2_receivables = repo.get_receivables_by_position("pos2")
        assert len(pos2_receivables) == 1
        assert pos2_receivables[0] == pos2_receivable

    def test_get_pending_receivables(self, repo):
        """Test getting pending receivables."""
        # Create receivables with different statuses
        pending_receivable = DividendReceivable(
            id="rec_pending",
            position_id="pos1",
            dividend_id="div1",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50"),
            status="pending"
        )
        
        paid_receivable = DividendReceivable(
            id="rec_paid",
            position_id="pos1",
            dividend_id="div2",
            shares_at_record=50.0,
            gross_amount=Decimal("41.00"),
            net_amount=Decimal("30.75"),
            withholding_tax=Decimal("10.25"),
            status="paid"
        )
        
        repo.create_receivable(pending_receivable)
        repo.create_receivable(paid_receivable)
        
        # Test getting pending receivables for pos1
        pending = repo.get_pending_receivables("pos1")
        assert len(pending) == 1
        assert pending[0] == pending_receivable

    def test_update_receivable(self, repo, sample_receivable):
        """Test updating a receivable."""
        # Create the receivable
        repo.create_receivable(sample_receivable)
        
        # Modify the receivable
        sample_receivable.status = "paid"
        sample_receivable.paid_at = datetime.now(timezone.utc)
        
        # Update it
        result = repo.update_receivable(sample_receivable)
        
        assert result == sample_receivable
        assert repo.get_receivable(sample_receivable.id).status == "paid"

    def test_mark_receivable_paid(self, repo, sample_receivable):
        """Test marking a receivable as paid."""
        # Create the receivable
        repo.create_receivable(sample_receivable)
        
        # Mark as paid
        result = repo.mark_receivable_paid(sample_receivable.id)
        
        assert result == sample_receivable
        assert sample_receivable.status == "paid"
        assert sample_receivable.paid_at is not None

    def test_mark_receivable_paid_nonexistent(self, repo):
        """Test marking a non-existent receivable as paid."""
        result = repo.mark_receivable_paid("nonexistent")
        assert result is None


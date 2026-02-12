# =========================
# backend/tests/unit/domain/test_dividend_entities.py
# =========================
from datetime import datetime, timezone
from decimal import Decimal

from domain.entities.dividend import Dividend, DividendReceivable


class TestDividend:
    """Test cases for Dividend entity."""

    def test_dividend_creation(self):
        """Test basic dividend creation."""
        ex_date = datetime(2024, 3, 15, tzinfo=timezone.utc)
        pay_date = datetime(2024, 3, 29, tzinfo=timezone.utc)
        
        dividend = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=ex_date,
            pay_date=pay_date,
            dps=Decimal("0.82"),
            currency="USD",
            withholding_tax_rate=0.25
        )
        
        assert dividend.id == "div_AAPL_20240315"
        assert dividend.ticker == "AAPL"
        assert dividend.ex_date == ex_date
        assert dividend.pay_date == pay_date
        assert dividend.dps == Decimal("0.82")
        assert dividend.currency == "USD"
        assert dividend.withholding_tax_rate == 0.25

    def test_dividend_defaults(self):
        """Test dividend creation with defaults."""
        ex_date = datetime(2024, 3, 15, tzinfo=timezone.utc)
        pay_date = datetime(2024, 3, 29, tzinfo=timezone.utc)
        
        dividend = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=ex_date,
            pay_date=pay_date,
            dps=Decimal("0.82")
        )
        
        assert dividend.currency == "USD"
        assert dividend.withholding_tax_rate == 0.25
        assert dividend.created_at is not None

    def test_calculate_gross_amount(self):
        """Test gross amount calculation."""
        dividend = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=datetime(2024, 3, 15, tzinfo=timezone.utc),
            pay_date=datetime(2024, 3, 29, tzinfo=timezone.utc),
            dps=Decimal("0.82")
        )
        
        # Test with 100 shares
        gross = dividend.calculate_gross_amount(100.0)
        assert gross == Decimal("82.00")
        
        # Test with fractional shares
        gross = dividend.calculate_gross_amount(50.5)
        assert gross == Decimal("41.41")

    def test_calculate_net_amount(self):
        """Test net amount calculation after withholding tax."""
        dividend = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=datetime(2024, 3, 15, tzinfo=timezone.utc),
            pay_date=datetime(2024, 3, 29, tzinfo=timezone.utc),
            dps=Decimal("0.82"),
            withholding_tax_rate=0.25
        )
        
        # Test with 100 shares
        net = dividend.calculate_net_amount(100.0)
        expected = Decimal("82.00") - (Decimal("82.00") * Decimal("0.25"))
        assert net == expected
        assert net == Decimal("61.50")

    def test_calculate_withholding_tax(self):
        """Test withholding tax calculation."""
        dividend = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=datetime(2024, 3, 15, tzinfo=timezone.utc),
            pay_date=datetime(2024, 3, 29, tzinfo=timezone.utc),
            dps=Decimal("0.82"),
            withholding_tax_rate=0.25
        )
        
        # Test with 100 shares
        withholding = dividend.calculate_withholding_tax(100.0)
        expected = Decimal("82.00") * Decimal("0.25")
        assert withholding == expected
        assert withholding == Decimal("20.50")

    def test_different_withholding_rates(self):
        """Test different withholding tax rates."""
        ex_date = datetime(2024, 3, 15, tzinfo=timezone.utc)
        pay_date = datetime(2024, 3, 29, tzinfo=timezone.utc)
        
        # 15% withholding
        dividend_15 = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=ex_date,
            pay_date=pay_date,
            dps=Decimal("1.00"),
            withholding_tax_rate=0.15
        )
        
        net_15 = dividend_15.calculate_net_amount(100.0)
        assert net_15 == Decimal("85.00")
        
        # 30% withholding
        dividend_30 = Dividend(
            id="div_AAPL_20240315",
            ticker="AAPL",
            ex_date=ex_date,
            pay_date=pay_date,
            dps=Decimal("1.00"),
            withholding_tax_rate=0.30
        )
        
        net_30 = dividend_30.calculate_net_amount(100.0)
        assert net_30 == Decimal("70.00")


class TestDividendReceivable:
    """Test cases for DividendReceivable entity."""

    def test_receivable_creation(self):
        """Test basic receivable creation."""
        receivable = DividendReceivable(
            id="rec_pos123_div456",
            position_id="pos123",
            dividend_id="div456",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50")
        )
        
        assert receivable.id == "rec_pos123_div456"
        assert receivable.position_id == "pos123"
        assert receivable.dividend_id == "div456"
        assert receivable.shares_at_record == 100.0
        assert receivable.gross_amount == Decimal("82.00")
        assert receivable.net_amount == Decimal("61.50")
        assert receivable.withholding_tax == Decimal("20.50")
        assert receivable.status == "pending"
        assert receivable.paid_at is None

    def test_receivable_defaults(self):
        """Test receivable creation with defaults."""
        receivable = DividendReceivable(
            id="rec_pos123_div456",
            position_id="pos123",
            dividend_id="div456",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50")
        )
        
        assert receivable.status == "pending"
        assert receivable.paid_at is None
        assert receivable.created_at is not None

    def test_mark_paid(self):
        """Test marking receivable as paid."""
        receivable = DividendReceivable(
            id="rec_pos123_div456",
            position_id="pos123",
            dividend_id="div456",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50")
        )
        
        assert receivable.status == "pending"
        assert receivable.paid_at is None
        
        receivable.mark_paid()
        
        assert receivable.status == "paid"
        assert receivable.paid_at is not None
        assert isinstance(receivable.paid_at, datetime)

    def test_mark_paid_twice(self):
        """Test marking receivable as paid multiple times."""
        receivable = DividendReceivable(
            id="rec_pos123_div456",
            position_id="pos123",
            dividend_id="div456",
            shares_at_record=100.0,
            gross_amount=Decimal("82.00"),
            net_amount=Decimal("61.50"),
            withholding_tax=Decimal("20.50")
        )
        
        datetime.now(timezone.utc)
        receivable.mark_paid()
        first_paid_time = receivable.paid_at
        
        # Mark as paid again
        receivable.mark_paid()
        
        # Should update the paid_at time
        assert receivable.status == "paid"
        assert receivable.paid_at is not None
        assert receivable.paid_at >= first_paid_time


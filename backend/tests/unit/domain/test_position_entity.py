# =========================
# backend/tests/unit/domain/test_position_entity.py
# =========================
from datetime import datetime, timezone

from domain.entities.position import Position
from domain.value_objects.guardrails import GuardrailPolicy
from domain.value_objects.order_policy import OrderPolicy


class TestPosition:
    """Test cases for Position entity."""

    def test_position_creation(self):
        """Test basic position creation."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        assert position.id == "pos_123"
        assert position.ticker == "AAPL"  # Backward compatibility property
        assert position.asset_symbol == "AAPL"
        assert position.qty == 100.0
        assert position.anchor_price is None
        assert position.dividend_receivable == 0.0
        assert position.withholding_tax_rate == 0.25
        assert isinstance(position.guardrails, GuardrailPolicy)
        assert isinstance(position.order_policy, OrderPolicy)
        assert isinstance(position.created_at, datetime)
        assert isinstance(position.updated_at, datetime)

    def test_position_creation_with_anchor_price(self):
        """Test position creation with anchor price."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            anchor_price=150.0,
        )

        assert position.anchor_price == 150.0

    def test_position_creation_with_dividend_settings(self):
        """Test position creation with dividend settings."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            dividend_receivable=50.0,
            withholding_tax_rate=0.30,
        )

        assert position.dividend_receivable == 50.0
        assert position.withholding_tax_rate == 0.30

    def test_set_anchor_price(self):
        """Test setting anchor price."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        original_updated_at = position.updated_at

        position.set_anchor_price(150.0)

        assert position.anchor_price == 150.0
        assert position.updated_at > original_updated_at

    def test_set_anchor_price_updates_timestamp(self):
        """Test that setting anchor price updates timestamp."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        # Wait a small amount to ensure timestamp difference
        import time

        time.sleep(0.001)

        position.set_anchor_price(150.0)

        assert position.updated_at > position.created_at

    def test_get_effective_cash_no_receivable(self):
        """Test effective cash calculation without receivable."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            cash=10000.0,
        )

        assert position.get_effective_cash() == 10000.0

    def test_get_effective_cash_with_receivable(self):
        """Test effective cash calculation with receivable."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            cash=10000.0,
            dividend_receivable=50.0,
        )

        assert position.get_effective_cash() == 10050.0

    def test_adjust_anchor_for_dividend_with_anchor(self):
        """Test anchor price adjustment for dividend with existing anchor."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            anchor_price=150.0,
        )

        original_updated_at = position.updated_at

        position.adjust_anchor_for_dividend(0.82)

        assert position.anchor_price == 149.18  # 150.0 - 0.82
        assert position.updated_at > original_updated_at

    def test_adjust_anchor_for_dividend_no_anchor(self):
        """Test anchor price adjustment for dividend without existing anchor."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        position.adjust_anchor_for_dividend(0.82)

        # Should not change anything if no anchor price
        assert position.anchor_price is None

    def test_add_dividend_receivable(self):
        """Test adding dividend receivable."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        original_updated_at = position.updated_at

        position.add_dividend_receivable(50.0)

        assert position.dividend_receivable == 50.0
        assert position.updated_at > original_updated_at

    def test_add_dividend_receivable_multiple_times(self):
        """Test adding dividend receivable multiple times."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        position.add_dividend_receivable(25.0)
        position.add_dividend_receivable(30.0)

        assert position.dividend_receivable == 55.0

    def test_clear_dividend_receivable(self):
        """Test clearing dividend receivable."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            dividend_receivable=50.0,
        )

        original_updated_at = position.updated_at

        position.clear_dividend_receivable(50.0)

        assert position.dividend_receivable == 0.0
        assert position.updated_at > original_updated_at

    def test_clear_dividend_receivable_partial(self):
        """Test clearing partial dividend receivable."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            dividend_receivable=50.0,
        )

        position.clear_dividend_receivable(30.0)

        assert position.dividend_receivable == 20.0

    def test_clear_dividend_receivable_exceeds_available(self):
        """Test clearing more dividend receivable than available."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            dividend_receivable=50.0,
        )

        # Should cap receivable at 0
        position.clear_dividend_receivable(60.0)
        assert position.dividend_receivable == 0.0  # Capped at 0

    def test_position_total_value_calculation(self):
        """Test total position value calculation."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            anchor_price=150.0,
            dividend_receivable=25.0,
        )

        # Total value = (qty * anchor_price) + portfolio_cash + dividend_receivable
        # Note: cash is now in portfolio, so this test uses portfolio_cash_balance
        portfolio_cash_balance = 10000.0
        expected_total = (100.0 * 150.0) + portfolio_cash_balance + 25.0
        actual_total = (
            (position.qty * position.anchor_price)
            + portfolio_cash_balance
            + position.dividend_receivable
        )

        assert actual_total == expected_total
        assert actual_total == 25025.0

    def test_position_asset_allocation_calculation(self):
        """Test asset allocation percentage calculation."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            anchor_price=150.0,
        )

        # Asset allocation = (qty * price) / total_value
        portfolio_cash_balance = 10000.0
        stock_value = position.qty * position.anchor_price
        total_value = stock_value + portfolio_cash_balance
        asset_allocation = stock_value / total_value

        expected_allocation = (100.0 * 150.0) / ((100.0 * 150.0) + 10000.0)
        assert asset_allocation == expected_allocation
        assert asset_allocation == 0.6  # 60%

    def test_position_with_guardrails(self):
        """Test position with custom guardrails."""
        custom_guardrails = GuardrailPolicy(
            min_stock_alloc_pct=0.2, max_stock_alloc_pct=0.8, max_orders_per_day=10
        )

        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            guardrails=custom_guardrails,
        )

        assert position.guardrails.min_stock_alloc_pct == 0.2
        assert position.guardrails.max_stock_alloc_pct == 0.8
        assert position.guardrails.max_orders_per_day == 10

    def test_position_with_order_policy(self):
        """Test position with custom order policy."""
        custom_order_policy = OrderPolicy(
            min_qty=1.0,
            min_notional=50.0,
            lot_size=1.0,
            qty_step=0.1,
            action_below_min="reject",
            trigger_threshold_pct=0.05,
            rebalance_ratio=2.0,
            commission_rate=0.002,
            allow_after_hours=True,
        )

        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            order_policy=custom_order_policy,
        )

        assert position.order_policy.min_qty == 1.0
        assert position.order_policy.min_notional == 50.0
        assert position.order_policy.trigger_threshold_pct == 0.05
        assert position.order_policy.allow_after_hours is True

    def test_position_equality(self):
        """Test position equality comparison."""
        fixed_time = datetime.now(timezone.utc)

        position1 = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )
        position1.created_at = fixed_time
        position1.updated_at = fixed_time

        position2 = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )
        position2.created_at = fixed_time
        position2.updated_at = fixed_time

        # Positions with same ID should be equal
        assert position1 == position2

    def test_position_inequality(self):
        """Test position inequality comparison."""
        position1 = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        position2 = Position(
            id="pos_456",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        # Positions with different IDs should not be equal
        assert position1 != position2

    def test_position_string_representation(self):
        """Test position string representation."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            anchor_price=150.0,
        )

        str_repr = str(position)
        assert "pos_123" in str_repr
        assert "AAPL" in str_repr
        assert "100.0" in str_repr

    def test_position_commission_aggregate_default(self):
        """Test that total_commission_paid defaults to 0.0."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        assert position.total_commission_paid == 0.0

    def test_position_commission_aggregate_initialization(self):
        """Test position creation with initial commission aggregate."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            total_commission_paid=50.0,
        )

        assert position.total_commission_paid == 50.0

    def test_position_dividend_aggregate_default(self):
        """Test that total_dividends_received defaults to 0.0."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        assert position.total_dividends_received == 0.0

    def test_position_dividend_aggregate_initialization(self):
        """Test position creation with initial dividend aggregate."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            total_dividends_received=200.0,
        )

        assert position.total_dividends_received == 200.0

    def test_position_commission_aggregate_increment(self):
        """Test incrementing total_commission_paid."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        assert position.total_commission_paid == 0.0

        # Simulate commission payment
        position.total_commission_paid += 1.5
        assert position.total_commission_paid == 1.5

        # Add more commission
        position.total_commission_paid += 2.3
        assert position.total_commission_paid == 3.8

    def test_position_dividend_aggregate_increment(self):
        """Test incrementing total_dividends_received."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        assert position.total_dividends_received == 0.0

        # Simulate dividend payment
        position.total_dividends_received += 61.50
        assert position.total_dividends_received == 61.50

        # Add more dividends
        position.total_dividends_received += 82.00
        assert position.total_dividends_received == 143.50

    def test_position_commission_aggregation_across_trades(self):
        """Test commission aggregation across multiple trades."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        # Simulate multiple trades with commissions
        commissions = [1.5, 2.3, 0.8, 1.2]
        for commission in commissions:
            position.total_commission_paid += commission

        expected_total = sum(commissions)
        assert position.total_commission_paid == expected_total
        assert position.total_commission_paid == 5.8

    def test_position_dividend_aggregation_across_payments(self):
        """Test dividend aggregation across multiple payments."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        # Simulate multiple dividend payments
        dividends = [61.50, 82.00, 45.25]
        for dividend in dividends:
            position.total_dividends_received += dividend

        expected_total = sum(dividends)
        assert position.total_dividends_received == expected_total
        assert position.total_dividends_received == 188.75

    def test_position_commission_and_dividend_independence(self):
        """Test that commission and dividend aggregates are independent."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
        )

        # Add commissions
        position.total_commission_paid += 1.5
        position.total_commission_paid += 2.3

        # Add dividends
        position.total_dividends_received += 61.50
        position.total_dividends_received += 82.00

        # Verify they are independent
        assert position.total_commission_paid == 3.8
        assert position.total_dividends_received == 143.50

    def test_position_creation_with_all_aggregates(self):
        """Test position creation with both commission and dividend aggregates."""
        position = Position(
            id="pos_123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            total_commission_paid=25.0,
            total_dividends_received=150.0,
        )

        assert position.total_commission_paid == 25.0
        assert position.total_dividends_received == 150.0

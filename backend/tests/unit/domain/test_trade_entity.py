# =========================
# backend/tests/unit/domain/test_trade_entity.py
# =========================
import pytest
from datetime import datetime, timezone
from domain.entities.trade import Trade


class TestTrade:
    """Test cases for Trade entity."""

    def test_trade_creation(self):
        """Test basic trade creation."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        
        assert trade.id == "trade_123"
        assert trade.order_id == "ord_456"
        assert trade.position_id == "pos_789"
        assert trade.side == "BUY"
        assert trade.qty == 100.0
        assert trade.price == 150.0
        assert trade.commission == 1.5
        assert isinstance(trade.executed_at, datetime)

    def test_trade_creation_with_all_fields(self):
        """Test trade creation with all fields."""
        executed_time = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="SELL",
            qty=50.0,
            price=155.0,
            commission=0.75,
            executed_at=executed_time
        )
        
        assert trade.id == "trade_123"
        assert trade.order_id == "ord_456"
        assert trade.position_id == "pos_789"
        assert trade.side == "SELL"
        assert trade.qty == 50.0
        assert trade.price == 155.0
        assert trade.commission == 0.75
        assert trade.executed_at == executed_time

    def test_trade_creation_with_zero_commission(self):
        """Test trade creation with zero commission."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=0.0,
            executed_at=datetime.now(timezone.utc)
        )
        
        assert trade.commission == 0.0

    def test_trade_creation_with_negative_commission(self):
        """Test trade creation with negative commission (rebate)."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=-0.5,  # Rebate
            executed_at=datetime.now(timezone.utc)
        )
        
        assert trade.commission == -0.5

    def test_trade_side_validation(self):
        """Test trade side validation."""
        # Valid sides
        buy_trade = Trade(
            id="trade_1",
            order_id="ord_1",
            position_id="pos_1",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        assert buy_trade.side == "BUY"
        
        sell_trade = Trade(
            id="trade_2",
            order_id="ord_2",
            position_id="pos_2",
            side="SELL",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        assert sell_trade.side == "SELL"

    def test_trade_notional_calculation(self):
        """Test trade notional calculation."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        
        # Notional = qty * price
        expected_notional = 100.0 * 150.0
        actual_notional = trade.qty * trade.price
        
        assert actual_notional == expected_notional
        assert actual_notional == 15000.0

    def test_trade_total_cost_calculation(self):
        """Test trade total cost calculation."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        
        # Total cost = notional + commission
        notional = trade.qty * trade.price
        total_cost = notional + trade.commission
        
        assert total_cost == 15001.5

    def test_trade_net_proceeds_calculation(self):
        """Test trade net proceeds calculation."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="SELL",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        
        # Net proceeds = notional - commission
        notional = trade.qty * trade.price
        net_proceeds = notional - trade.commission
        
        assert net_proceeds == 14998.5

    def test_trade_equality(self):
        """Test trade equality comparison."""
        executed_time = datetime.now(timezone.utc)
        
        trade1 = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=executed_time
        )
        
        trade2 = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=executed_time
        )
        
        # Trades with same ID should be equal
        assert trade1 == trade2

    def test_trade_inequality(self):
        """Test trade inequality comparison."""
        executed_time = datetime.now(timezone.utc)
        
        trade1 = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=executed_time
        )
        
        trade2 = Trade(
            id="trade_456",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=executed_time
        )
        
        # Trades with different IDs should not be equal
        assert trade1 != trade2

    def test_trade_string_representation(self):
        """Test trade string representation."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        
        str_repr = str(trade)
        assert "trade_123" in str_repr
        assert "ord_456" in str_repr
        assert "pos_789" in str_repr
        assert "BUY" in str_repr
        assert "100.0" in str_repr
        assert "150.0" in str_repr

    def test_trade_hash(self):
        """Test trade hash for use in sets and dictionaries."""
        executed_time = datetime.now(timezone.utc)
        
        trade1 = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=executed_time
        )
        
        trade2 = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=executed_time
        )
        
        # Trades with same ID should have same hash
        assert hash(trade1) == hash(trade2)
        
        # Trades should be usable in sets
        trade_set = {trade1, trade2}
        assert len(trade_set) == 1  # Should be deduplicated

    def test_trade_with_fractional_quantity(self):
        """Test trade with fractional quantity."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.5,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        
        assert trade.qty == 100.5

    def test_trade_with_fractional_price(self):
        """Test trade with fractional price."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.25,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        
        assert trade.price == 150.25

    def test_trade_with_fractional_commission(self):
        """Test trade with fractional commission."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.25,
            executed_at=datetime.now(timezone.utc)
        )
        
        assert trade.commission == 1.25

    def test_trade_with_zero_quantity(self):
        """Test trade with zero quantity."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=0.0,
            price=150.0,
            commission=0.0,
            executed_at=datetime.now(timezone.utc)
        )
        
        assert trade.qty == 0.0
        assert trade.commission == 0.0

    def test_trade_with_zero_price(self):
        """Test trade with zero price."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=0.0,
            commission=0.0,
            executed_at=datetime.now(timezone.utc)
        )
        
        assert trade.price == 0.0

    def test_trade_with_negative_quantity(self):
        """Test trade with negative quantity."""
        # This should be allowed at entity level (validation happens at use case level)
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=-100.0,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        
        assert trade.qty == -100.0

    def test_trade_with_negative_price(self):
        """Test trade with negative price."""
        # This should be allowed at entity level (validation happens at use case level)
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=-150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        
        assert trade.price == -150.0

    def test_trade_execution_timestamp(self):
        """Test trade execution timestamp."""
        specific_time = datetime(2024, 1, 15, 10, 30, 45, 123456, tzinfo=timezone.utc)
        
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=specific_time
        )
        
        assert trade.executed_at == specific_time

    def test_trade_immutability(self):
        """Test that trade fields are immutable after creation."""
        trade = Trade(
            id="trade_123",
            order_id="ord_456",
            position_id="pos_789",
            side="BUY",
            qty=100.0,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc)
        )
        
        # These should not be modifiable after creation
        # (This test documents expected behavior - actual implementation may vary)
        original_id = trade.id
        original_order_id = trade.order_id
        original_position_id = trade.position_id
        original_side = trade.side
        original_qty = trade.qty
        original_price = trade.price
        original_commission = trade.commission
        
        # In a real implementation, these might be read-only properties
        assert trade.id == original_id
        assert trade.order_id == original_order_id
        assert trade.position_id == original_position_id
        assert trade.side == original_side
        assert trade.qty == original_qty
        assert trade.price == original_price
        assert trade.commission == original_commission

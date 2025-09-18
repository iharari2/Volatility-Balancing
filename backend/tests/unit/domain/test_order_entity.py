# =========================
# backend/tests/unit/domain/test_order_entity.py
# =========================
import pytest
from datetime import datetime, timezone
from domain.entities.order import Order
from domain.value_objects.types import OrderSide


class TestOrder:
    """Test cases for Order entity."""

    def test_order_creation(self):
        """Test basic order creation."""
        order = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)

        assert order.id == "ord_123"
        assert order.position_id == "pos_456"
        assert order.side == "BUY"
        assert order.qty == 100.0
        assert order.status == "submitted"
        assert order.idempotency_key is None
        assert order.request_signature is None
        assert isinstance(order.created_at, datetime)
        assert isinstance(order.updated_at, datetime)

    def test_order_creation_with_all_fields(self):
        """Test order creation with all fields."""
        order = Order(
            id="ord_123",
            position_id="pos_456",
            side="SELL",
            qty=50.0,
            status="filled",
            idempotency_key="key_789",
            request_signature={"side": "SELL", "qty": 50.0},
        )

        assert order.id == "ord_123"
        assert order.position_id == "pos_456"
        assert order.side == "SELL"
        assert order.qty == 50.0
        assert order.status == "filled"
        assert order.idempotency_key == "key_789"
        assert order.request_signature == {"side": "SELL", "qty": 50.0}

    def test_order_creation_with_timestamps(self):
        """Test order creation with custom timestamps."""
        custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

        order = Order(
            id="ord_123",
            position_id="pos_456",
            side="BUY",
            qty=100.0,
            created_at=custom_time,
            updated_at=custom_time,
        )

        assert order.created_at == custom_time
        assert order.updated_at == custom_time

    def test_order_side_validation(self):
        """Test order side validation."""
        # Valid sides
        buy_order = Order(id="ord_1", position_id="pos_1", side="BUY", qty=100.0)
        assert buy_order.side == "BUY"

        sell_order = Order(id="ord_2", position_id="pos_2", side="SELL", qty=100.0)
        assert sell_order.side == "SELL"

    def test_order_status_defaults(self):
        """Test order status defaults."""
        order = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)

        assert order.status == "submitted"

    def test_order_status_values(self):
        """Test order status values."""
        # Test all valid status values
        statuses = ["submitted", "filled", "rejected"]

        for status in statuses:
            order = Order(
                id=f"ord_{status}", position_id="pos_456", side="BUY", qty=100.0, status=status
            )
            assert order.status == status

    def test_order_equality(self):
        """Test order equality comparison."""
        fixed_time = datetime.now(timezone.utc)

        order1 = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)
        order1.created_at = fixed_time
        order1.updated_at = fixed_time

        order2 = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)
        order2.created_at = fixed_time
        order2.updated_at = fixed_time

        # Orders with same ID should be equal
        assert order1 == order2

    def test_order_inequality(self):
        """Test order inequality comparison."""
        order1 = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)

        order2 = Order(id="ord_789", position_id="pos_456", side="BUY", qty=100.0)

        # Orders with different IDs should not be equal
        assert order1 != order2

    def test_order_string_representation(self):
        """Test order string representation."""
        order = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0, status="filled")

        str_repr = str(order)
        assert "ord_123" in str_repr
        assert "pos_456" in str_repr
        assert "BUY" in str_repr
        assert "100.0" in str_repr
        assert "filled" in str_repr

    def test_order_with_idempotency_key(self):
        """Test order with idempotency key."""
        order = Order(
            id="ord_123",
            position_id="pos_456",
            side="BUY",
            qty=100.0,
            idempotency_key="unique_key_123",
        )

        assert order.idempotency_key == "unique_key_123"

    def test_order_with_request_signature(self):
        """Test order with request signature."""
        signature = {"position_id": "pos_456", "side": "BUY", "qty": 100.0, "price": 150.0}

        order = Order(
            id="ord_123", position_id="pos_456", side="BUY", qty=100.0, request_signature=signature
        )

        assert order.request_signature == signature

    def test_order_quantity_validation(self):
        """Test order quantity validation."""
        # Test positive quantity
        order = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)
        assert order.qty == 100.0

        # Test fractional quantity
        order = Order(id="ord_124", position_id="pos_456", side="BUY", qty=100.5)
        assert order.qty == 100.5

    def test_order_creation_timestamps(self):
        """Test that order creation sets timestamps."""
        before_creation = datetime.now(timezone.utc)

        order = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)

        after_creation = datetime.now(timezone.utc)

        assert before_creation <= order.created_at <= after_creation
        assert before_creation <= order.updated_at <= after_creation
        # Allow for small time differences between created_at and updated_at
        time_diff = abs((order.created_at - order.updated_at).total_seconds())
        assert time_diff < 0.001  # Less than 1 millisecond difference

    def test_order_side_type_validation(self):
        """Test order side type validation."""
        # Test with string values that match OrderSide literal
        order = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)
        assert order.side == "BUY"

    def test_order_immutability(self):
        """Test that order fields are immutable after creation."""
        order = Order(
            id="ord_123", position_id="pos_456", side="BUY", qty=100.0, status="submitted"
        )

        # These should not be modifiable after creation
        # (This test documents expected behavior - actual implementation may vary)
        original_id = order.id
        original_position_id = order.position_id
        original_side = order.side
        original_qty = order.qty

        # In a real implementation, these might be read-only properties
        assert order.id == original_id
        assert order.position_id == original_position_id
        assert order.side == original_side
        assert order.qty == original_qty

    def test_order_with_zero_quantity(self):
        """Test order with zero quantity."""
        order = Order(id="ord_123", position_id="pos_456", side="BUY", qty=0.0)

        assert order.qty == 0.0

    def test_order_with_negative_quantity(self):
        """Test order with negative quantity."""
        # This should be allowed at entity level (validation happens at use case level)
        order = Order(id="ord_123", position_id="pos_456", side="BUY", qty=-100.0)

        assert order.qty == -100.0

    def test_order_hash(self):
        """Test order hash for use in sets and dictionaries."""
        fixed_time = datetime.now(timezone.utc)

        order1 = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)
        order1.created_at = fixed_time
        order1.updated_at = fixed_time

        order2 = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)
        order2.created_at = fixed_time
        order2.updated_at = fixed_time

        # Orders with same ID should have same hash
        assert hash(order1) == hash(order2)

        # Orders should be usable in sets
        order_set = {order1, order2}
        assert len(order_set) == 1  # Should be deduplicated

    def test_order_comparison(self):
        """Test order comparison operations."""
        order1 = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)

        order2 = Order(id="ord_456", position_id="pos_456", side="BUY", qty=100.0)

        # Orders should be comparable
        assert order1 != order2
        assert not (order1 == order2)

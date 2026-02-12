# =========================
# backend/tests/unit/domain/test_event_entity.py
# =========================
from datetime import datetime, timezone
from domain.entities.event import Event


class TestEvent:
    """Test cases for Event entity."""

    def test_event_creation(self):
        """Test basic event creation."""
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="order_submitted",
            inputs={"side": "BUY", "qty": 100.0},
            outputs={"order_id": "ord_789"},
            message="Order submitted successfully",
            ts=datetime.now(timezone.utc)
        )
        
        assert event.id == "evt_123"
        assert event.position_id == "pos_456"
        assert event.type == "order_submitted"
        assert event.inputs == {"side": "BUY", "qty": 100.0}
        assert event.outputs == {"order_id": "ord_789"}
        assert event.message == "Order submitted successfully"
        assert isinstance(event.ts, datetime)

    def test_event_creation_with_minimal_data(self):
        """Test event creation with minimal required data."""
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="test_event",
            inputs={},
            outputs={},
            message="Test message",
            ts=datetime.now(timezone.utc)
        )
        
        assert event.id == "evt_123"
        assert event.position_id == "pos_456"
        assert event.type == "test_event"
        assert event.inputs == {}
        assert event.outputs == {}
        assert event.message == "Test message"

    def test_event_creation_with_complex_data(self):
        """Test event creation with complex input/output data."""
        complex_inputs = {
            "position_id": "pos_456",
            "order_details": {
                "side": "BUY",
                "qty": 100.0,
                "price": 150.0
            },
            "market_data": {
                "current_price": 149.50,
                "is_market_hours": True
            },
            "validation_results": {
                "valid": True,
                "warnings": [],
                "rejections": []
            }
        }
        
        complex_outputs = {
            "order_id": "ord_789",
            "execution_price": 149.50,
            "commission": 0.15,
            "total_cost": 14965.15,
            "new_position_qty": 100.0,
            "new_cash_balance": 85034.85
        }
        
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="order_filled",
            inputs=complex_inputs,
            outputs=complex_outputs,
            message="Order filled at market price",
            ts=datetime.now(timezone.utc)
        )
        
        assert event.inputs == complex_inputs
        assert event.outputs == complex_outputs

    def test_event_creation_with_different_types(self):
        """Test event creation with different event types."""
        event_types = [
            "order_submitted",
            "order_filled",
            "order_rejected",
            "position_created",
            "anchor_price_set",
            "dividend_announced",
            "dividend_processed",
            "guardrail_breach",
            "market_data_updated",
            "simulation_completed"
        ]
        
        for event_type in event_types:
            event = Event(
                id=f"evt_{event_type}",
                position_id="pos_456",
                type=event_type,
                inputs={"test": "data"},
                outputs={"result": "success"},
                message=f"Test {event_type} event",
                ts=datetime.now(timezone.utc)
            )
            
            assert event.type == event_type

    def test_event_creation_with_timestamp(self):
        """Test event creation with specific timestamp."""
        specific_time = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="test_event",
            inputs={},
            outputs={},
            message="Test message",
            ts=specific_time
        )
        
        assert event.ts == specific_time

    def test_event_creation_with_none_values(self):
        """Test event creation with None values in inputs/outputs."""
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="test_event",
            inputs={"null_value": None, "empty_string": ""},
            outputs={"result": None},
            message="Test message with None values",
            ts=datetime.now(timezone.utc)
        )
        
        assert event.inputs["null_value"] is None
        assert event.inputs["empty_string"] == ""
        assert event.outputs["result"] is None

    def test_event_creation_with_numeric_data(self):
        """Test event creation with numeric data."""
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="calculation_completed",
            inputs={
                "price": 150.0,
                "qty": 100,
                "commission_rate": 0.001
            },
            outputs={
                "total_cost": 15015.0,
                "commission": 15.0,
                "net_proceeds": 14985.0
            },
            message="Calculation completed",
            ts=datetime.now(timezone.utc)
        )
        
        assert event.inputs["price"] == 150.0
        assert event.inputs["qty"] == 100
        assert event.outputs["total_cost"] == 15015.0

    def test_event_creation_with_boolean_data(self):
        """Test event creation with boolean data."""
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="validation_completed",
            inputs={
                "is_market_hours": True,
                "is_fresh_data": False,
                "allow_after_hours": True
            },
            outputs={
                "validation_passed": True,
                "warnings_generated": False
            },
            message="Validation completed",
            ts=datetime.now(timezone.utc)
        )
        
        assert event.inputs["is_market_hours"] is True
        assert event.inputs["is_fresh_data"] is False
        assert event.outputs["validation_passed"] is True

    def test_event_creation_with_list_data(self):
        """Test event creation with list data."""
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="batch_processing_completed",
            inputs={
                "order_ids": ["ord_1", "ord_2", "ord_3"],
                "prices": [150.0, 151.0, 149.5]
            },
            outputs={
                "processed_orders": 3,
                "successful_orders": 2,
                "failed_orders": 1,
                "failed_order_ids": ["ord_2"]
            },
            message="Batch processing completed",
            ts=datetime.now(timezone.utc)
        )
        
        assert event.inputs["order_ids"] == ["ord_1", "ord_2", "ord_3"]
        assert event.outputs["processed_orders"] == 3

    def test_event_equality(self):
        """Test event equality comparison."""
        timestamp = datetime.now(timezone.utc)
        
        event1 = Event(
            id="evt_123",
            position_id="pos_456",
            type="test_event",
            inputs={"key": "value"},
            outputs={"result": "success"},
            message="Test message",
            ts=timestamp
        )
        
        event2 = Event(
            id="evt_123",
            position_id="pos_456",
            type="test_event",
            inputs={"key": "value"},
            outputs={"result": "success"},
            message="Test message",
            ts=timestamp
        )
        
        # Events with same ID should be equal
        assert event1 == event2

    def test_event_inequality(self):
        """Test event inequality comparison."""
        timestamp = datetime.now(timezone.utc)
        
        event1 = Event(
            id="evt_123",
            position_id="pos_456",
            type="test_event",
            inputs={},
            outputs={},
            message="Test message",
            ts=timestamp
        )
        
        event2 = Event(
            id="evt_456",
            position_id="pos_456",
            type="test_event",
            inputs={},
            outputs={},
            message="Test message",
            ts=timestamp
        )
        
        # Events with different IDs should not be equal
        assert event1 != event2

    def test_event_string_representation(self):
        """Test event string representation."""
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="order_filled",
            inputs={"side": "BUY"},
            outputs={"order_id": "ord_789"},
            message="Order filled successfully",
            ts=datetime.now(timezone.utc)
        )
        
        str_repr = str(event)
        assert "evt_123" in str_repr
        assert "pos_456" in str_repr
        assert "order_filled" in str_repr

    def test_event_hash(self):
        """Test event hash for use in sets and dictionaries."""
        timestamp = datetime.now(timezone.utc)
        
        event1 = Event(
            id="evt_123",
            position_id="pos_456",
            type="test_event",
            inputs={},
            outputs={},
            message="Test message",
            ts=timestamp
        )
        
        event2 = Event(
            id="evt_123",
            position_id="pos_456",
            type="test_event",
            inputs={},
            outputs={},
            message="Test message",
            ts=timestamp
        )
        
        # Events with same ID should have same hash
        assert hash(event1) == hash(event2)
        
        # Events should be usable in sets
        event_set = {event1, event2}
        assert len(event_set) == 1  # Should be deduplicated

    def test_event_with_empty_message(self):
        """Test event with empty message."""
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="test_event",
            inputs={},
            outputs={},
            message="",
            ts=datetime.now(timezone.utc)
        )
        
        assert event.message == ""

    def test_event_with_long_message(self):
        """Test event with long message."""
        long_message = "This is a very long message that contains detailed information about what happened during the event processing. It might include error details, debugging information, or other verbose output that helps with troubleshooting and monitoring."
        
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="detailed_event",
            inputs={},
            outputs={},
            message=long_message,
            ts=datetime.now(timezone.utc)
        )
        
        assert event.message == long_message

    def test_event_with_special_characters(self):
        """Test event with special characters in message."""
        special_message = "Event with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="special_event",
            inputs={},
            outputs={},
            message=special_message,
            ts=datetime.now(timezone.utc)
        )
        
        assert event.message == special_message

    def test_event_with_unicode_characters(self):
        """Test event with unicode characters."""
        unicode_message = "Event with unicode: 你好世界 🌍 émojis 🚀"
        
        event = Event(
            id="evt_123",
            position_id="pos_456",
            type="unicode_event",
            inputs={},
            outputs={},
            message=unicode_message,
            ts=datetime.now(timezone.utc)
        )
        
        assert event.message == unicode_message

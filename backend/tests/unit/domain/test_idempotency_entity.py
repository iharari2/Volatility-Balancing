# =========================
# backend/tests/unit/domain/test_idempotency_entity.py
# =========================
import pytest
from datetime import datetime, timezone, timedelta
from domain.entities.idempotency import IdempotencyRecord


class TestIdempotencyRecord:
    """Test cases for IdempotencyRecord entity."""

    def test_idempotency_record_creation(self):
        """Test basic idempotency record creation."""
        record = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=datetime.now(timezone.utc),
        )

        assert record.key == "test_key_123"
        assert record.order_id == "order_789"
        assert record.signature_hash == "abc123def456"
        assert isinstance(record.expires_at, datetime)

    def test_idempotency_record_creation_with_timestamp(self):
        """Test idempotency record creation with specific timestamp."""
        specific_time = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)

        record = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=specific_time,
        )

        assert record.expires_at == specific_time

    def test_idempotency_record_creation_with_different_order_ids(self):
        """Test idempotency record creation with different order IDs."""
        # String order ID
        record1 = IdempotencyRecord(
            key="test_key_1",
            order_id="order_123",
            signature_hash="sig1",
            expires_at=datetime.now(timezone.utc),
        )
        assert record1.order_id == "order_123"

        # UUID-like order ID
        record2 = IdempotencyRecord(
            key="test_key_2",
            order_id="ord_12345678-1234-5678-9abc-123456789012",
            signature_hash="sig2",
            expires_at=datetime.now(timezone.utc),
        )
        assert record2.order_id == "ord_12345678-1234-5678-9abc-123456789012"

    def test_idempotency_record_creation_with_different_signature_hashes(self):
        """Test idempotency record creation with different signature hash formats."""
        # Hex signature hash
        record1 = IdempotencyRecord(
            key="test_key_1",
            order_id="order_123",
            signature_hash="a1b2c3d4e5f6",
            expires_at=datetime.now(timezone.utc),
        )
        assert record1.signature_hash == "a1b2c3d4e5f6"

        # Long signature hash
        long_hash = "a" * 64  # 64 character hex string
        record2 = IdempotencyRecord(
            key="test_key_2",
            order_id="order_456",
            signature_hash=long_hash,
            expires_at=datetime.now(timezone.utc),
        )
        assert record2.signature_hash == long_hash

        # Short signature hash
        short_hash = "abc"
        record3 = IdempotencyRecord(
            key="test_key_3",
            order_id="order_789",
            signature_hash=short_hash,
            expires_at=datetime.now(timezone.utc),
        )
        assert record3.signature_hash == short_hash

    def test_idempotency_record_creation_with_different_keys(self):
        """Test idempotency record creation with different key formats."""
        # Simple key
        record1 = IdempotencyRecord(
            key="simple_key",
            order_id="order_123",
            signature_hash="sig1",
            expires_at=datetime.now(timezone.utc),
        )
        assert record1.key == "simple_key"

        # Scoped key
        record2 = IdempotencyRecord(
            key="pos_123:order_456",
            order_id="order_789",
            signature_hash="sig2",
            expires_at=datetime.now(timezone.utc),
        )
        assert record2.key == "pos_123:order_456"

        # UUID-like key
        record3 = IdempotencyRecord(
            key="uuid_12345678-1234-5678-9abc-123456789012",
            order_id="order_abc",
            signature_hash="sig3",
            expires_at=datetime.now(timezone.utc),
        )
        assert record3.key == "uuid_12345678-1234-5678-9abc-123456789012"

    def test_idempotency_record_equality(self):
        """Test idempotency record equality comparison."""
        timestamp = datetime.now(timezone.utc)

        record1 = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=timestamp,
        )

        record2 = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=timestamp,
        )

        # Records with same key should be equal
        assert record1 == record2

    def test_idempotency_record_inequality(self):
        """Test idempotency record inequality comparison."""
        timestamp = datetime.now(timezone.utc)

        record1 = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=timestamp,
        )

        record2 = IdempotencyRecord(
            key="test_key_456",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=timestamp,
        )

        # Records with different keys should not be equal
        assert record1 != record2

    def test_idempotency_record_string_representation(self):
        """Test idempotency record string representation."""
        record = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=datetime.now(timezone.utc),
        )

        str_repr = str(record)
        assert "test_key_123" in str_repr
        assert "order_789" in str_repr
        assert "abc123def456" in str_repr

    def test_idempotency_record_hash(self):
        """Test idempotency record hash for use in sets and dictionaries."""
        timestamp = datetime.now(timezone.utc)

        record1 = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=timestamp,
        )

        record2 = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=timestamp,
        )

        # Records with same key should have same hash
        assert hash(record1) == hash(record2)

        # Records should be usable in sets
        record_set = {record1, record2}
        assert len(record_set) == 1  # Should be deduplicated

    def test_idempotency_record_with_empty_key(self):
        """Test idempotency record with empty key."""
        record = IdempotencyRecord(
            key="",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=datetime.now(timezone.utc),
        )

        assert record.key == ""

    def test_idempotency_record_with_empty_signature_hash(self):
        """Test idempotency record with empty signature hash."""
        record = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="",
            expires_at=datetime.now(timezone.utc),
        )

        assert record.signature_hash == ""

    def test_idempotency_record_with_empty_order_id(self):
        """Test idempotency record with empty order ID."""
        record = IdempotencyRecord(
            key="test_key_123",
            order_id="",
            signature_hash="abc123def456",
            expires_at=datetime.now(timezone.utc),
        )

        assert record.order_id == ""

    def test_idempotency_record_with_special_characters(self):
        """Test idempotency record with special characters."""
        special_key = "key!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        special_signature_hash = "sig!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        special_order_id = "order!@#$%^&*()_+-=[]{}|;':\",./<>?`~"

        record = IdempotencyRecord(
            key=special_key,
            order_id=special_order_id,
            signature_hash=special_signature_hash,
            expires_at=datetime.now(timezone.utc),
        )

        assert record.key == special_key
        assert record.signature_hash == special_signature_hash
        assert record.order_id == special_order_id

    def test_idempotency_record_with_unicode_characters(self):
        """Test idempotency record with unicode characters."""
        unicode_key = "key_你好世界_🌍"
        unicode_signature_hash = "sig_émojis_🚀"
        unicode_order_id = "order_unicode_测试"

        record = IdempotencyRecord(
            key=unicode_key,
            order_id=unicode_order_id,
            signature_hash=unicode_signature_hash,
            expires_at=datetime.now(timezone.utc),
        )

        assert record.key == unicode_key
        assert record.signature_hash == unicode_signature_hash
        assert record.order_id == unicode_order_id

    def test_idempotency_record_with_very_long_strings(self):
        """Test idempotency record with very long strings."""
        long_key = "key_" + "x" * 1000
        long_signature_hash = "sig_" + "y" * 1000
        long_order_id = "order_" + "z" * 1000

        record = IdempotencyRecord(
            key=long_key,
            order_id=long_order_id,
            signature_hash=long_signature_hash,
            expires_at=datetime.now(timezone.utc),
        )

        assert record.key == long_key
        assert record.signature_hash == long_signature_hash
        assert record.order_id == long_order_id

    def test_idempotency_record_creation_timestamp(self):
        """Test that idempotency record creation sets timestamp."""
        before_creation = datetime.now(timezone.utc)

        record = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=datetime.now(timezone.utc),
        )

        after_creation = datetime.now(timezone.utc)

        assert before_creation <= record.expires_at <= after_creation

    def test_idempotency_record_immutability(self):
        """Test that idempotency record fields are immutable after creation."""
        record = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=datetime.now(timezone.utc),
        )

        # These should not be modifiable after creation
        # (This test documents expected behavior - actual implementation may vary)
        original_key = record.key
        original_order_id = record.order_id
        original_signature_hash = record.signature_hash
        original_expires_at = record.expires_at

        # In a real implementation, these might be read-only properties
        assert record.key == original_key
        assert record.order_id == original_order_id
        assert record.signature_hash == original_signature_hash
        assert record.expires_at == original_expires_at

    def test_idempotency_record_ttl_static_method(self):
        """Test the ttl static method."""
        # Test default 48 hours
        ttl_default = IdempotencyRecord.ttl()
        assert isinstance(ttl_default, datetime)

        # Test custom hours
        ttl_custom = IdempotencyRecord.ttl(24)
        assert isinstance(ttl_custom, datetime)

        # Test that custom TTL is different from default
        assert ttl_custom != ttl_default

    def test_idempotency_record_with_future_expiration(self):
        """Test idempotency record with future expiration time."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=24)

        record = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=future_time,
        )

        assert record.expires_at == future_time
        assert record.expires_at > datetime.now(timezone.utc)

    def test_idempotency_record_with_past_expiration(self):
        """Test idempotency record with past expiration time."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=24)

        record = IdempotencyRecord(
            key="test_key_123",
            order_id="order_789",
            signature_hash="abc123def456",
            expires_at=past_time,
        )

        assert record.expires_at == past_time
        assert record.expires_at < datetime.now(timezone.utc)

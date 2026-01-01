# =========================
# backend/tests/unit/infrastructure/test_config_repo_sql.py
# =========================
"""Unit tests for SQLConfigRepo."""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.ports.config_repo import ConfigScope
from domain.value_objects.configs import TriggerConfig, GuardrailConfig, OrderPolicyConfig
from infrastructure.persistence.sql.config_repo_sql import SQLConfigRepo
from infrastructure.persistence.sql.models import (
    CommissionRateModel,
    TriggerConfigModel,
    GuardrailConfigModel,
    OrderPolicyConfigModel,
)


@pytest.fixture
def sql_engine():
    """Create an in-memory SQLite engine for testing."""
    # Use a unique in-memory database for each test to avoid conflicts
    # SQLite :memory: databases are isolated per connection
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create only the config tables we need (not all Base.metadata tables)
    # This avoids conflicts with other tables that might have duplicate indexes
    with engine.begin() as conn:
        CommissionRateModel.__table__.create(conn, checkfirst=True)
        TriggerConfigModel.__table__.create(conn, checkfirst=True)
        GuardrailConfigModel.__table__.create(conn, checkfirst=True)
        OrderPolicyConfigModel.__table__.create(conn, checkfirst=True)

    yield engine

    # Cleanup - drop only the config tables
    with engine.begin() as conn:
        OrderPolicyConfigModel.__table__.drop(conn, checkfirst=True)
        GuardrailConfigModel.__table__.drop(conn, checkfirst=True)
        TriggerConfigModel.__table__.drop(conn, checkfirst=True)
        CommissionRateModel.__table__.drop(conn, checkfirst=True)


@pytest.fixture
def session_factory(sql_engine):
    """Create a session factory."""
    return sessionmaker(bind=sql_engine, expire_on_commit=False, autoflush=False)


@pytest.fixture
def config_repo(session_factory):
    """Create a SQLConfigRepo instance."""
    return SQLConfigRepo(session_factory)


class TestSQLConfigRepo_CommissionRates:
    """Test commission rate operations."""

    def test_get_default_global_commission_rate(self, config_repo):
        """Test that default global commission rate is initialized."""
        rate = config_repo.get_commission_rate()
        assert rate == 0.0001  # Default 0.01%

    def test_set_and_get_global_commission_rate(self, config_repo):
        """Test setting and getting global commission rate."""
        config_repo.set_commission_rate(0.0002, ConfigScope.GLOBAL)
        rate = config_repo.get_commission_rate()
        assert rate == 0.0002

    def test_set_and_get_tenant_commission_rate(self, config_repo):
        """Test setting and getting tenant commission rate."""
        tenant_id = "T1"
        config_repo.set_commission_rate(0.0003, ConfigScope.TENANT, tenant_id=tenant_id)

        # Should return tenant rate when tenant_id provided
        rate = config_repo.get_commission_rate(tenant_id=tenant_id)
        assert rate == 0.0003

        # Should fall back to global when tenant_id not provided
        global_rate = config_repo.get_commission_rate()
        assert global_rate == 0.0001  # Default global

    def test_set_and_get_tenant_asset_commission_rate(self, config_repo):
        """Test setting and getting tenant-asset commission rate."""
        tenant_id = "T1"
        asset_id = "AAPL"
        config_repo.set_commission_rate(
            0.0004, ConfigScope.TENANT_ASSET, tenant_id=tenant_id, asset_id=asset_id
        )

        # Should return tenant-asset rate when both provided
        rate = config_repo.get_commission_rate(tenant_id=tenant_id, asset_id=asset_id)
        assert rate == 0.0004

        # Should fall back to tenant rate when only tenant_id provided
        tenant_rate = config_repo.get_commission_rate(tenant_id=tenant_id)
        assert tenant_rate == 0.0001  # Falls back to global (no tenant rate set)

        # Should fall back to global when neither provided
        global_rate = config_repo.get_commission_rate()
        assert global_rate == 0.0001

    def test_hierarchical_commission_rate_lookup(self, config_repo):
        """Test hierarchical lookup: TENANT_ASSET -> TENANT -> GLOBAL."""
        tenant_id = "T1"
        asset_id = "AAPL"

        # Set all three levels
        config_repo.set_commission_rate(0.0010, ConfigScope.GLOBAL)
        config_repo.set_commission_rate(0.0020, ConfigScope.TENANT, tenant_id=tenant_id)
        config_repo.set_commission_rate(
            0.0030, ConfigScope.TENANT_ASSET, tenant_id=tenant_id, asset_id=asset_id
        )

        # Should get tenant-asset rate (most specific)
        rate = config_repo.get_commission_rate(tenant_id=tenant_id, asset_id=asset_id)
        assert rate == 0.0030

        # Should get tenant rate (less specific)
        rate = config_repo.get_commission_rate(tenant_id=tenant_id)
        assert rate == 0.0020

        # Should get global rate (least specific)
        rate = config_repo.get_commission_rate()
        assert rate == 0.0010

    def test_update_existing_commission_rate(self, config_repo):
        """Test updating an existing commission rate."""
        config_repo.set_commission_rate(0.0005, ConfigScope.GLOBAL)
        assert config_repo.get_commission_rate() == 0.0005

        # Update it
        config_repo.set_commission_rate(0.0006, ConfigScope.GLOBAL)
        assert config_repo.get_commission_rate() == 0.0006


class TestSQLConfigRepo_TriggerConfigs:
    """Test trigger configuration operations."""

    def test_set_and_get_trigger_config(self, config_repo):
        """Test setting and getting trigger config."""
        position_id = "pos123"
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )

        config_repo.set_trigger_config(position_id, trigger_config)
        result = config_repo.get_trigger_config(position_id)

        assert result is not None
        assert result.up_threshold_pct == Decimal("3.0")
        assert result.down_threshold_pct == Decimal("3.0")

    def test_get_nonexistent_trigger_config(self, config_repo):
        """Test getting non-existent trigger config."""
        result = config_repo.get_trigger_config("nonexistent")
        assert result is None

    def test_update_trigger_config(self, config_repo):
        """Test updating existing trigger config."""
        position_id = "pos123"
        initial_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        config_repo.set_trigger_config(position_id, initial_config)

        # Update it
        updated_config = TriggerConfig(
            up_threshold_pct=Decimal("5.0"),
            down_threshold_pct=Decimal("5.0"),
        )
        config_repo.set_trigger_config(position_id, updated_config)

        result = config_repo.get_trigger_config(position_id)
        assert result.up_threshold_pct == Decimal("5.0")
        assert result.down_threshold_pct == Decimal("5.0")

    def test_multiple_trigger_configs(self, config_repo):
        """Test multiple positions with different trigger configs."""
        pos1_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        pos2_config = TriggerConfig(
            up_threshold_pct=Decimal("5.0"),
            down_threshold_pct=Decimal("5.0"),
        )

        config_repo.set_trigger_config("pos1", pos1_config)
        config_repo.set_trigger_config("pos2", pos2_config)

        assert config_repo.get_trigger_config("pos1").up_threshold_pct == Decimal("3.0")
        assert config_repo.get_trigger_config("pos2").up_threshold_pct == Decimal("5.0")


class TestSQLConfigRepo_GuardrailConfigs:
    """Test guardrail configuration operations."""

    def test_set_and_get_guardrail_config(self, config_repo):
        """Test setting and getting guardrail config."""
        position_id = "pos123"
        guardrail_config = GuardrailConfig(
            min_stock_pct=Decimal("0"),
            max_stock_pct=Decimal("50"),
            max_trade_pct_of_position=Decimal("10"),
            max_daily_notional=Decimal("10000"),
            max_orders_per_day=5,
        )

        config_repo.set_guardrail_config(position_id, guardrail_config)
        result = config_repo.get_guardrail_config(position_id)

        assert result is not None
        assert result.min_stock_pct == Decimal("0")
        assert result.max_stock_pct == Decimal("50")
        assert result.max_trade_pct_of_position == Decimal("10")
        assert result.max_daily_notional == Decimal("10000")
        assert result.max_orders_per_day == 5

    def test_get_nonexistent_guardrail_config(self, config_repo):
        """Test getting non-existent guardrail config."""
        result = config_repo.get_guardrail_config("nonexistent")
        assert result is None

    def test_guardrail_config_with_optional_fields_none(self, config_repo):
        """Test guardrail config with optional fields set to None."""
        position_id = "pos123"
        guardrail_config = GuardrailConfig(
            min_stock_pct=Decimal("0"),
            max_stock_pct=Decimal("100"),
            max_trade_pct_of_position=None,
            max_daily_notional=None,
            max_orders_per_day=None,
        )

        config_repo.set_guardrail_config(position_id, guardrail_config)
        result = config_repo.get_guardrail_config(position_id)

        assert result is not None
        assert result.min_stock_pct == Decimal("0")
        assert result.max_stock_pct == Decimal("100")
        assert result.max_trade_pct_of_position is None
        assert result.max_daily_notional is None
        assert result.max_orders_per_day is None

    def test_update_guardrail_config(self, config_repo):
        """Test updating existing guardrail config."""
        position_id = "pos123"
        initial_config = GuardrailConfig(
            min_stock_pct=Decimal("0"),
            max_stock_pct=Decimal("50"),
        )
        config_repo.set_guardrail_config(position_id, initial_config)

        # Update it
        updated_config = GuardrailConfig(
            min_stock_pct=Decimal("10"),
            max_stock_pct=Decimal("90"),
            max_orders_per_day=10,
        )
        config_repo.set_guardrail_config(position_id, updated_config)

        result = config_repo.get_guardrail_config(position_id)
        assert result.min_stock_pct == Decimal("10")
        assert result.max_stock_pct == Decimal("90")
        assert result.max_orders_per_day == 10


class TestSQLConfigRepo_OrderPolicyConfigs:
    """Test order policy configuration operations."""

    def test_set_and_get_order_policy_config(self, config_repo):
        """Test setting and getting order policy config."""
        position_id = "pos123"
        order_policy_config = OrderPolicyConfig(
            min_qty=Decimal("1"),
            min_notional=Decimal("100.0"),
            lot_size=Decimal("0"),
            qty_step=Decimal("0"),
            action_below_min="hold",
            rebalance_ratio=Decimal("1.6667"),
            order_sizing_strategy="proportional",
            allow_after_hours=True,
            commission_rate=Decimal("0.001"),
        )

        config_repo.set_order_policy_config(position_id, order_policy_config)
        result = config_repo.get_order_policy_config(position_id)

        assert result is not None
        assert result.min_qty == Decimal("1")
        assert result.min_notional == Decimal("100.0")
        assert result.action_below_min == "hold"
        assert result.rebalance_ratio == Decimal("1.6667")
        assert result.order_sizing_strategy == "proportional"
        assert result.allow_after_hours is True
        assert result.commission_rate == Decimal("0.001")

    def test_get_nonexistent_order_policy_config(self, config_repo):
        """Test getting non-existent order policy config."""
        result = config_repo.get_order_policy_config("nonexistent")
        assert result is None

    def test_order_policy_config_with_optional_commission_rate_none(self, config_repo):
        """Test order policy config with commission_rate set to None."""
        position_id = "pos123"
        order_policy_config = OrderPolicyConfig(
            min_qty=Decimal("0"),
            min_notional=Decimal("100.0"),
            commission_rate=None,
        )

        config_repo.set_order_policy_config(position_id, order_policy_config)
        result = config_repo.get_order_policy_config(position_id)

        assert result is not None
        assert result.commission_rate is None

    def test_order_policy_config_defaults(self, config_repo):
        """Test order policy config with default values."""
        position_id = "pos123"
        order_policy_config = OrderPolicyConfig(
            min_qty=Decimal("0"),
            min_notional=Decimal("100.0"),
        )

        config_repo.set_order_policy_config(position_id, order_policy_config)
        result = config_repo.get_order_policy_config(position_id)

        assert result is not None
        assert result.min_qty == Decimal("0")  # Default
        assert result.min_notional == Decimal("100.0")  # Default
        assert result.action_below_min == "hold"  # Default
        assert result.allow_after_hours is True  # Default

    def test_update_order_policy_config(self, config_repo):
        """Test updating existing order policy config."""
        position_id = "pos123"
        initial_config = OrderPolicyConfig(
            min_notional=Decimal("100.0"),
            allow_after_hours=True,
        )
        config_repo.set_order_policy_config(position_id, initial_config)

        # Update it
        updated_config = OrderPolicyConfig(
            min_notional=Decimal("200.0"),
            allow_after_hours=False,
        )
        config_repo.set_order_policy_config(position_id, updated_config)

        result = config_repo.get_order_policy_config(position_id)
        assert result.min_notional == Decimal("200.0")
        assert result.allow_after_hours is False


class TestSQLConfigRepo_Integration:
    """Integration tests for multiple config types."""

    def test_multiple_config_types_for_same_position(self, config_repo):
        """Test storing multiple config types for the same position."""
        position_id = "pos123"

        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )
        guardrail_config = GuardrailConfig(
            min_stock_pct=Decimal("0"),
            max_stock_pct=Decimal("50"),
        )
        order_policy_config = OrderPolicyConfig(
            min_notional=Decimal("100.0"),
        )

        config_repo.set_trigger_config(position_id, trigger_config)
        config_repo.set_guardrail_config(position_id, guardrail_config)
        config_repo.set_order_policy_config(position_id, order_policy_config)

        # Verify all can be retrieved
        assert config_repo.get_trigger_config(position_id) is not None
        assert config_repo.get_guardrail_config(position_id) is not None
        assert config_repo.get_order_policy_config(position_id) is not None

    def test_persistence_across_sessions(self, sql_engine, session_factory):
        """Test that configs persist across different sessions."""
        position_id = "pos123"
        trigger_config = TriggerConfig(
            up_threshold_pct=Decimal("3.0"),
            down_threshold_pct=Decimal("3.0"),
        )

        # Create first repo and set config
        repo1 = SQLConfigRepo(session_factory)
        repo1.set_trigger_config(position_id, trigger_config)

        # Create second repo and get config
        repo2 = SQLConfigRepo(session_factory)
        result = repo2.get_trigger_config(position_id)

        assert result is not None
        assert result.up_threshold_pct == Decimal("3.0")
        assert result.down_threshold_pct == Decimal("3.0")

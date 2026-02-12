# =========================
# backend/tests/unit/application/test_submit_order_uc.py
# =========================
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from application.use_cases.submit_order_uc import SubmitOrderUC
from application.dto.orders import CreateOrderRequest, CreateOrderResponse
from domain.entities.order import Order
from domain.entities.position import Position
from domain.entities.event import Event
from domain.errors import IdempotencyConflict, PositionNotFound, GuardrailBreach
from domain.ports.config_repo import ConfigRepo


class TestSubmitOrderUC:
    """Test cases for SubmitOrderUC."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "positions_repo": Mock(),
            "orders_repo": Mock(),
            "idempotency_repo": Mock(),
            "events_repo": Mock(),
            "config_repo": Mock(spec=ConfigRepo),
            "clock": Mock(),
        }

    @pytest.fixture
    def submit_order_uc(self, mock_repos):
        """Create SubmitOrderUC with mock dependencies."""
        from domain.value_objects.configs import GuardrailConfig

        # Create a default guardrail config provider
        def guardrail_provider(tenant_id: str, portfolio_id: str, pos_id: str) -> GuardrailConfig:
            from decimal import Decimal

            return GuardrailConfig(
                min_stock_pct=Decimal("0"),
                max_stock_pct=Decimal("100"),
            )  # Default config

        return SubmitOrderUC(
            positions=mock_repos["positions_repo"],
            orders=mock_repos["orders_repo"],
            idempotency=mock_repos["idempotency_repo"],
            events=mock_repos["events_repo"],
            config_repo=mock_repos["config_repo"],
            clock=mock_repos["clock"],
            guardrail_config_provider=guardrail_provider,
        )

    @pytest.fixture
    def sample_position(self):
        """Create a sample position."""
        from domain.value_objects.guardrails import GuardrailPolicy
        from domain.value_objects.order_policy import OrderPolicy

        return Position(
            id="pos123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            anchor_price=150.0,
            guardrails=GuardrailPolicy(),
            order_policy=OrderPolicy(commission_rate=0.0001),
        )

    def test_submit_order_success(self, submit_order_uc, mock_repos, sample_position):
        """Test successful order submission."""
        # Arrange
        position_id = "pos123"
        request = CreateOrderRequest(side="BUY", qty=10.0)
        idempotency_key = "test-key-123"

        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["idempotency_repo"].reserve.return_value = None  # No existing order
        mock_repos["orders_repo"].count_for_position_on_day.return_value = 0
        mock_repos["config_repo"].get_commission_rate.return_value = 0.0001
        mock_repos["clock"].now.return_value = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Act
        result = submit_order_uc.execute(
            tenant_id="default",
            portfolio_id="test_portfolio",
            position_id=position_id,
            request=request,
            idempotency_key=idempotency_key,
        )

        # Assert
        assert isinstance(result, CreateOrderResponse)
        assert result.accepted is True
        assert result.position_id == position_id
        assert result.order_id is not None

        # Verify order was created with commission snapshot
        mock_repos["orders_repo"].save.assert_called_once()
        saved_order = mock_repos["orders_repo"].save.call_args[0][0]
        assert isinstance(saved_order, Order)
        assert saved_order.commission_rate_snapshot == 0.0001
        assert saved_order.commission_estimated is None  # Price not available at order creation

        # Verify config_repo was called
        mock_repos["config_repo"].get_commission_rate.assert_called_once_with(
            tenant_id="default", asset_id="AAPL"
        )

    def test_submit_order_commission_rate_snapshot(
        self, submit_order_uc, mock_repos, sample_position
    ):
        """Test that commission rate snapshot is stored in order."""
        # Arrange
        position_id = "pos123"
        request = CreateOrderRequest(side="BUY", qty=10.0)
        idempotency_key = "test-key-123"
        commission_rate = 0.0002  # Different rate

        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["idempotency_repo"].reserve.return_value = None
        mock_repos["orders_repo"].count_for_position_on_day.return_value = 0
        mock_repos["config_repo"].get_commission_rate.return_value = commission_rate
        mock_repos["clock"].now.return_value = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Act
        submit_order_uc.execute(
            tenant_id="default",
            portfolio_id="test_portfolio",
            position_id=position_id,
            request=request,
            idempotency_key=idempotency_key,
        )

        # Assert
        saved_order = mock_repos["orders_repo"].save.call_args[0][0]
        assert saved_order.commission_rate_snapshot == commission_rate

    def test_submit_order_commission_rate_from_config_repo(
        self, submit_order_uc, mock_repos, sample_position
    ):
        """Test that commission rate is fetched from config_repo."""
        # Arrange
        position_id = "pos123"
        request = CreateOrderRequest(side="BUY", qty=10.0)
        idempotency_key = "test-key-123"
        expected_rate = 0.0003

        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["idempotency_repo"].reserve.return_value = None
        mock_repos["orders_repo"].count_for_position_on_day.return_value = 0
        mock_repos["config_repo"].get_commission_rate.return_value = expected_rate
        mock_repos["clock"].now.return_value = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Act
        submit_order_uc.execute(
            tenant_id="default",
            portfolio_id="test_portfolio",
            position_id=position_id,
            request=request,
            idempotency_key=idempotency_key,
        )

        # Assert
        mock_repos["config_repo"].get_commission_rate.assert_called_once_with(
            tenant_id="default", asset_id="AAPL"
        )
        saved_order = mock_repos["orders_repo"].save.call_args[0][0]
        assert saved_order.commission_rate_snapshot == expected_rate

    def test_submit_order_commission_rate_fallback_to_order_policy(
        self, submit_order_uc, mock_repos
    ):
        """Test that commission rate falls back to OrderPolicy if config doesn't match."""
        # Arrange
        from domain.value_objects.guardrails import GuardrailPolicy
        from domain.value_objects.order_policy import OrderPolicy

        position = Position(
            id="pos123",
            tenant_id="default",
            portfolio_id="test_portfolio",
            asset_symbol="AAPL",
            qty=100.0,
            guardrails=GuardrailPolicy(),
            order_policy=OrderPolicy(commission_rate=0.0005),  # Different from default
        )

        position_id = "pos123"
        request = CreateOrderRequest(side="BUY", qty=10.0)
        idempotency_key = "test-key-123"

        mock_repos["positions_repo"].get.return_value = position
        mock_repos["idempotency_repo"].reserve.return_value = None
        mock_repos["orders_repo"].count_for_position_on_day.return_value = 0
        mock_repos["config_repo"].get_commission_rate.return_value = 0.0001  # Default from config
        mock_repos["clock"].now.return_value = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Act
        submit_order_uc.execute(
            tenant_id="default",
            portfolio_id="test_portfolio",
            position_id=position_id,
            request=request,
            idempotency_key=idempotency_key,
        )

        # Assert - Should use OrderPolicy rate since it differs from default
        saved_order = mock_repos["orders_repo"].save.call_args[0][0]
        assert saved_order.commission_rate_snapshot == 0.0005  # From OrderPolicy

    def test_submit_order_commission_estimated_none(
        self, submit_order_uc, mock_repos, sample_position
    ):
        """Test that commission_estimated is None when price is not available."""
        # Arrange
        position_id = "pos123"
        request = CreateOrderRequest(side="BUY", qty=10.0)
        idempotency_key = "test-key-123"

        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["idempotency_repo"].reserve.return_value = None
        mock_repos["orders_repo"].count_for_position_on_day.return_value = 0
        mock_repos["config_repo"].get_commission_rate.return_value = 0.0001
        mock_repos["clock"].now.return_value = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Act
        submit_order_uc.execute(
            tenant_id="default",
            portfolio_id="test_portfolio",
            position_id=position_id,
            request=request,
            idempotency_key=idempotency_key,
        )

        # Assert
        saved_order = mock_repos["orders_repo"].save.call_args[0][0]
        assert saved_order.commission_estimated is None  # Price not in CreateOrderRequest

    def test_submit_order_position_not_found(self, submit_order_uc, mock_repos):
        """Test order submission when position doesn't exist."""
        # Arrange
        position_id = "nonexistent"
        request = CreateOrderRequest(side="BUY", qty=10.0)
        idempotency_key = "test-key-123"

        mock_repos["positions_repo"].get.return_value = None

        # Act & Assert
        with pytest.raises(PositionNotFound):
            submit_order_uc.execute(
                tenant_id="default",
                portfolio_id="test_portfolio",
                position_id=position_id,
                request=request,
                idempotency_key=idempotency_key,
            )

    def test_submit_order_idempotency_conflict(self, submit_order_uc, mock_repos, sample_position):
        """Test order submission with idempotency conflict."""
        # Arrange
        position_id = "pos123"
        request = CreateOrderRequest(side="BUY", qty=10.0)
        idempotency_key = "test-key-123"

        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["idempotency_repo"].reserve.return_value = "conflict:different_signature"

        # Act & Assert
        with pytest.raises(IdempotencyConflict):
            submit_order_uc.execute(
                tenant_id="default",
                portfolio_id="test_portfolio",
                position_id=position_id,
                request=request,
                idempotency_key=idempotency_key,
            )

    def test_submit_order_daily_cap_exceeded(self, submit_order_uc, mock_repos, sample_position):
        """Test order submission when daily cap is exceeded."""
        # Arrange
        from domain.value_objects.configs import GuardrailConfig

        position_id = "pos123"
        request = CreateOrderRequest(side="BUY", qty=10.0)
        idempotency_key = "test-key-123"

        # Set up guardrail config with max_orders_per_day
        from decimal import Decimal

        guardrail_config = GuardrailConfig(
            min_stock_pct=Decimal("0"),
            max_stock_pct=Decimal("100"),
            max_orders_per_day=10,
        )

        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["idempotency_repo"].reserve.return_value = None
        mock_repos["orders_repo"].count_for_position_on_day.return_value = 10  # Max orders
        mock_repos["config_repo"].get_commission_rate.return_value = 0.0001

        # Create a guardrail_config_provider that returns the config
        def guardrail_provider(tenant_id: str, portfolio_id: str, pos_id: str) -> GuardrailConfig:
            return guardrail_config

        # Update the use case with the provider
        submit_order_uc.guardrail_config_provider = guardrail_provider

        # Act & Assert
        with pytest.raises(GuardrailBreach):
            submit_order_uc.execute(
                tenant_id="default",
                portfolio_id="test_portfolio",
                position_id=position_id,
                request=request,
                idempotency_key=idempotency_key,
            )

    def test_submit_order_event_created(self, submit_order_uc, mock_repos, sample_position):
        """Test that order submission creates an event."""
        # Arrange
        position_id = "pos123"
        request = CreateOrderRequest(side="BUY", qty=10.0)
        idempotency_key = "test-key-123"

        mock_repos["positions_repo"].get.return_value = sample_position
        mock_repos["idempotency_repo"].reserve.return_value = None
        mock_repos["orders_repo"].count_for_position_on_day.return_value = 0
        mock_repos["config_repo"].get_commission_rate.return_value = 0.0001
        mock_repos["clock"].now.return_value = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Act
        submit_order_uc.execute(
            tenant_id="default",
            portfolio_id="test_portfolio",
            position_id=position_id,
            request=request,
            idempotency_key=idempotency_key,
        )

        # Assert
        mock_repos["events_repo"].append.assert_called_once()
        event = mock_repos["events_repo"].append.call_args[0][0]
        assert isinstance(event, Event)
        assert event.type == "order_submitted"
        assert event.position_id == position_id

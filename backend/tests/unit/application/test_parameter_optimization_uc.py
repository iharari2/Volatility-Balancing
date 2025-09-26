# =========================
# backend/tests/unit/application/test_parameter_optimization_uc.py
# =========================

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, patch

from application.use_cases.parameter_optimization_uc import (
    ParameterOptimizationUC,
    CreateOptimizationRequest,
    OptimizationProgress,
)
from domain.entities.optimization_config import OptimizationConfig, OptimizationStatus
from domain.entities.optimization_result import (
    OptimizationResult,
    OptimizationResultStatus,
    ParameterCombination,
)
from domain.value_objects.optimization_criteria import OptimizationCriteria, OptimizationMetric
from domain.value_objects.parameter_range import ParameterRange, ParameterType


class TestCreateOptimizationRequest:
    def test_create_optimization_request_creation(self):
        """Test creating a create optimization request."""
        created_by = uuid4()
        now = datetime.now(timezone.utc)

        param_ranges = {
            "trigger_threshold": ParameterRange(
                min_value=0.01,
                max_value=0.05,
                step_size=0.01,
                parameter_type=ParameterType.FLOAT,
                name="trigger_threshold",
                description="Price movement percentage that triggers a rebalancing trade",
            )
        }

        criteria = OptimizationCriteria(
            primary_metric=OptimizationMetric.TOTAL_RETURN,
            secondary_metrics=[OptimizationMetric.SHARPE_RATIO],
            constraints=[],
            weights={
                OptimizationMetric.TOTAL_RETURN: 1.0,
                OptimizationMetric.SHARPE_RATIO: 0.5,
            },
        )

        request = CreateOptimizationRequest(
            name="Test Optimization",
            ticker="AAPL",
            start_date=now,
            end_date=datetime(2025, 1, 1),
            parameter_ranges=param_ranges,
            optimization_criteria=criteria,
            created_by=created_by,
            description="Test optimization request",
            max_combinations=100,
            batch_size=10,
        )

        assert request.name == "Test Optimization"
        assert request.ticker == "AAPL"
        assert request.created_by == created_by
        assert request.max_combinations == 100
        assert request.batch_size == 10


class TestOptimizationProgress:
    def test_optimization_progress_creation(self):
        """Test creating optimization progress."""
        config_id = uuid4()
        progress = OptimizationProgress(
            config_id=config_id,
            total_combinations=100,
            completed_combinations=25,
            failed_combinations=5,
            status="running",
        )

        assert progress.config_id == config_id
        assert progress.total_combinations == 100
        assert progress.completed_combinations == 25
        assert progress.failed_combinations == 5
        assert progress.status == "running"

    def test_optimization_progress_calculate_remaining(self):
        """Test calculating remaining combinations."""
        progress = OptimizationProgress(
            config_id=uuid4(),
            total_combinations=100,
            completed_combinations=25,
            failed_combinations=5,
            status="running",
        )

        # Remaining = 100 - 25 - 5 = 70
        assert progress.remaining_combinations == 70

    def test_optimization_progress_calculate_percentage(self):
        """Test calculating completion percentage."""
        progress = OptimizationProgress(
            config_id=uuid4(),
            total_combinations=100,
            completed_combinations=30,
            failed_combinations=10,
            status="running",
        )

        # Percentage = (30 + 10) / 100 = 40%
        assert progress.progress_percentage == 40.0


class TestParameterOptimizationUC:
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config_repo = Mock()
        self.mock_result_repo = Mock()
        self.mock_heatmap_repo = Mock()
        self.mock_simulation_service = Mock()

        self.uc = ParameterOptimizationUC(
            config_repo=self.mock_config_repo,
            result_repo=self.mock_result_repo,
            heatmap_repo=self.mock_heatmap_repo,
            simulation_repo=self.mock_simulation_service,
        )

    def test_create_optimization_config(self):
        """Test creating an optimization configuration."""
        # Setup
        request = self._create_test_request()

        # Execute
        result = self.uc.create_optimization_config(request)

        # Verify
        assert result.name == request.name
        assert result.ticker == request.ticker
        assert result.status == OptimizationStatus.DRAFT
        assert result.created_by == request.created_by
        self.mock_config_repo.save.assert_called_once()

        # Verify the saved config has correct properties
        saved_config = self.mock_config_repo.save.call_args[0][0]
        assert saved_config.name == request.name
        assert saved_config.ticker == request.ticker
        assert saved_config.status == OptimizationStatus.DRAFT

    def test_run_optimization(self):
        """Test running an optimization."""
        # Setup
        config_id = uuid4()
        config = self._create_test_config()
        config.status = OptimizationStatus.DRAFT
        self.mock_config_repo.get_by_id.return_value = config
        self.mock_result_repo.get_by_config.return_value = []

        # Execute
        self.uc.run_optimization(config_id)

        # Verify
        # Should be called twice: once for running, once for completed
        assert self.mock_config_repo.update_status.call_count == 2
        self.mock_config_repo.update_status.assert_any_call(
            config_id, OptimizationStatus.RUNNING.value
        )
        self.mock_config_repo.update_status.assert_any_call(
            config.id, OptimizationStatus.COMPLETED.value
        )

    def test_run_optimization_config_not_found(self):
        """Test running optimization for non-existent config."""
        # Setup
        config_id = uuid4()
        self.mock_config_repo.get_by_id.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match="Optimization config not found"):
            self.uc.run_optimization(config_id)

    def test_run_optimization_already_running(self):
        """Test running optimization that's already running."""
        # Setup
        config_id = uuid4()
        config = self._create_test_config()
        config.status = OptimizationStatus.RUNNING
        self.mock_config_repo.get_by_id.return_value = config

        # Execute & Verify
        with pytest.raises(ValueError, match="Cannot start optimization in status"):
            self.uc.run_optimization(config_id)

    def test_get_optimization_progress(self):
        """Test getting optimization progress."""
        # Setup
        config_id = uuid4()
        config = self._create_test_config()
        config.status = OptimizationStatus.RUNNING
        self.mock_config_repo.get_by_id.return_value = config

        # Mock results
        results = [
            self._create_test_result("test_001", OptimizationResultStatus.COMPLETED),
            self._create_test_result("test_002", OptimizationResultStatus.COMPLETED),
            self._create_test_result("test_003", OptimizationResultStatus.FAILED),
            self._create_test_result("test_004", OptimizationResultStatus.PENDING),
        ]
        self.mock_result_repo.get_by_config.return_value = results

        # Execute
        progress = self.uc.get_optimization_progress(config_id)

        # Verify
        assert progress.config_id == config_id
        assert progress.total_combinations == config.calculate_total_combinations()
        assert progress.completed_combinations == 2
        assert progress.failed_combinations == 1

    def test_get_optimization_progress_not_running(self):
        """Test getting progress for non-running optimization."""
        # Setup
        config_id = uuid4()
        config = self._create_test_config()
        config.status = OptimizationStatus.DRAFT
        self.mock_config_repo.get_by_id.return_value = config
        self.mock_result_repo.get_by_config.return_value = []

        # Execute & Verify
        with pytest.raises(ValueError, match="Optimization is not running"):
            self.uc.get_optimization_progress(config_id)

    def test_get_optimization_results(self):
        """Test getting optimization results."""
        # Setup
        config_id = uuid4()
        expected_results = [
            self._create_test_result("test_001", OptimizationResultStatus.COMPLETED),
            self._create_test_result("test_002", OptimizationResultStatus.COMPLETED),
        ]
        self.mock_result_repo.get_completed_results.return_value = expected_results

        # Execute
        results = self.uc.get_optimization_results(config_id)

        # Verify
        assert results == expected_results
        self.mock_result_repo.get_completed_results.assert_called_once_with(config_id)

    def _create_test_request(self) -> CreateOptimizationRequest:
        """Helper to create a test request."""
        param_ranges = {
            "trigger_threshold": ParameterRange(
                min_value=0.01,
                max_value=0.05,
                step_size=0.01,
                parameter_type=ParameterType.FLOAT,
                name="trigger_threshold",
                description="Price movement percentage that triggers a rebalancing trade",
            )
        }

        criteria = OptimizationCriteria(
            primary_metric=OptimizationMetric.TOTAL_RETURN,
            secondary_metrics=[OptimizationMetric.SHARPE_RATIO],
            constraints=[],
            weights={
                OptimizationMetric.TOTAL_RETURN: 1.0,
                OptimizationMetric.SHARPE_RATIO: 0.5,
            },
        )

        return CreateOptimizationRequest(
            name="Test Optimization",
            ticker="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2025, 1, 1),
            parameter_ranges=param_ranges,
            optimization_criteria=criteria,
            created_by=uuid4(),
            description="Test optimization request",
            max_combinations=100,
            batch_size=10,
        )

    def _create_test_config(self) -> OptimizationConfig:
        """Helper to create a test configuration."""
        param_ranges = {
            "trigger_threshold": ParameterRange(
                min_value=0.01,
                max_value=0.05,
                step_size=0.01,
                parameter_type=ParameterType.FLOAT,
                name="trigger_threshold",
                description="Price movement percentage that triggers a rebalancing trade",
            )
        }

        criteria = OptimizationCriteria(
            primary_metric=OptimizationMetric.TOTAL_RETURN,
            secondary_metrics=[OptimizationMetric.SHARPE_RATIO],
            constraints=[],
            weights={
                OptimizationMetric.TOTAL_RETURN: 1.0,
                OptimizationMetric.SHARPE_RATIO: 0.5,
            },
        )

        return OptimizationConfig(
            id=uuid4(),
            name="Test Config",
            ticker="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2025, 1, 1),
            parameter_ranges=param_ranges,
            optimization_criteria=criteria,
            status=OptimizationStatus.DRAFT,
            created_by=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def _create_test_result(
        self, combination_id: str, status: OptimizationResultStatus, metrics: dict = None
    ) -> OptimizationResult:
        """Helper to create a test result."""
        if metrics is None:
            metrics = {OptimizationMetric.TOTAL_RETURN: 0.15, OptimizationMetric.SHARPE_RATIO: 1.2}

        combination = ParameterCombination(
            parameters={"trigger_threshold": 0.02},
            combination_id=combination_id,
            created_at=datetime.now(timezone.utc),
        )

        result = OptimizationResult(
            id=uuid4(),
            config_id=uuid4(),
            parameter_combination=combination,
            metrics=metrics,
            status=status,
        )

        if status == OptimizationResultStatus.COMPLETED:
            result.mark_completed()
        elif status == OptimizationResultStatus.FAILED:
            result.mark_failed("Test error")

        return result

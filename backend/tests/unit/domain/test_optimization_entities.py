# =========================
# backend/tests/unit/domain/test_optimization_entities.py
# =========================

import pytest
from datetime import datetime
from uuid import uuid4
from domain.entities.optimization_config import OptimizationConfig, OptimizationStatus
from domain.entities.optimization_result import (
    OptimizationResult,
    OptimizationResultStatus,
    ParameterCombination,
    OptimizationResults,
)
from domain.value_objects.optimization_criteria import (
    OptimizationCriteria,
    OptimizationMetric,
)
from domain.value_objects.parameter_range import ParameterRange, ParameterType


class TestParameterCombination:
    def test_parameter_combination_creation(self):
        """Test creating a parameter combination."""
        combination = ParameterCombination(
            parameters={"trigger_threshold": 0.02, "rebalance_ratio": 1.5},
            combination_id="test_001",
            created_at=datetime.utcnow(),
        )

        assert combination.parameters == {"trigger_threshold": 0.02, "rebalance_ratio": 1.5}
        assert combination.combination_id == "test_001"
        assert isinstance(combination.created_at, datetime)

    def test_parameter_combination_validation_empty_parameters(self):
        """Test validation fails with empty parameters."""
        with pytest.raises(ValueError, match="Parameters cannot be empty"):
            ParameterCombination(
                parameters={},
                combination_id="test_001",
                created_at=datetime.utcnow(),
            )

    def test_parameter_combination_validation_empty_id(self):
        """Test validation fails with empty combination ID."""
        with pytest.raises(ValueError, match="Combination ID cannot be empty"):
            ParameterCombination(
                parameters={"trigger_threshold": 0.02},
                combination_id="",
                created_at=datetime.utcnow(),
            )


class TestOptimizationResult:
    def test_optimization_result_creation(self):
        """Test creating an optimization result."""
        config_id = uuid4()
        combination = ParameterCombination(
            parameters={"trigger_threshold": 0.02},
            combination_id="test_001",
            created_at=datetime.utcnow(),
        )

        result = OptimizationResult(
            id=uuid4(),
            config_id=config_id,
            parameter_combination=combination,
            metrics={OptimizationMetric.TOTAL_RETURN: 0.15, OptimizationMetric.SHARPE_RATIO: 1.2},
        )

        assert result.config_id == config_id
        assert result.parameter_combination == combination
        assert result.metrics[OptimizationMetric.TOTAL_RETURN] == 0.15
        assert result.status == OptimizationResultStatus.PENDING
        assert result.created_at is not None

    def test_optimization_result_mark_completed(self):
        """Test marking a result as completed."""
        result = self._create_test_result()

        result.mark_completed(execution_time=5.5)

        assert result.status == OptimizationResultStatus.COMPLETED
        assert result.completed_at is not None
        assert result.execution_time_seconds == 5.5

    def test_optimization_result_mark_failed(self):
        """Test marking a result as failed."""
        result = self._create_test_result()

        result.mark_failed("Simulation error")

        assert result.status == OptimizationResultStatus.FAILED
        assert result.error_message == "Simulation error"
        assert result.completed_at is not None

    def test_optimization_result_get_metric_value(self):
        """Test getting metric values."""
        result = self._create_test_result()

        assert result.get_metric_value(OptimizationMetric.TOTAL_RETURN) == 0.15
        assert result.get_metric_value(OptimizationMetric.VOLATILITY) is None

    def test_optimization_result_validation_empty_metrics_for_completed(self):
        """Test validation fails for completed result with empty metrics."""
        # Create a result with empty metrics and completed status - this should fail in __post_init__
        with pytest.raises(ValueError, match="Metrics cannot be empty for non-pending results"):
            OptimizationResult(
                id=uuid4(),
                config_id=uuid4(),
                parameter_combination=ParameterCombination(
                    parameters={"trigger_threshold": 0.02},
                    combination_id="test_001",
                    created_at=datetime.utcnow(),
                ),
                metrics={},
                status=OptimizationResultStatus.COMPLETED,
            )

    def _create_test_result(self) -> OptimizationResult:
        """Helper to create a test result."""
        combination = ParameterCombination(
            parameters={"trigger_threshold": 0.02},
            combination_id="test_001",
            created_at=datetime.utcnow(),
        )

        return OptimizationResult(
            id=uuid4(),
            config_id=uuid4(),
            parameter_combination=combination,
            metrics={OptimizationMetric.TOTAL_RETURN: 0.15, OptimizationMetric.SHARPE_RATIO: 1.2},
        )


class TestOptimizationResults:
    def test_optimization_results_creation(self):
        """Test creating a collection of optimization results."""
        config_id = uuid4()
        results = [
            self._create_test_result(OptimizationMetric.TOTAL_RETURN, 0.10),
            self._create_test_result(OptimizationMetric.TOTAL_RETURN, 0.20),
            self._create_test_result(OptimizationMetric.TOTAL_RETURN, 0.15),
        ]

        collection = OptimizationResults(
            config_id=config_id,
            results=results,
        )

        assert collection.config_id == config_id
        assert len(collection.results) == 3
        assert collection.best_result is not None
        assert collection.worst_result is not None
        assert collection.created_at is not None
        assert collection.updated_at is not None

    def test_optimization_results_find_best_worst(self):
        """Test finding best and worst results."""
        results = [
            self._create_test_result(OptimizationMetric.TOTAL_RETURN, 0.10),
            self._create_test_result(OptimizationMetric.TOTAL_RETURN, 0.30),
            self._create_test_result(OptimizationMetric.TOTAL_RETURN, 0.20),
        ]

        collection = OptimizationResults(config_id=uuid4(), results=results)

        # Best should be the one with highest total return (0.30)
        assert collection.best_result.metrics[OptimizationMetric.TOTAL_RETURN] == 0.30
        # Worst should be the one with lowest total return (0.10)
        assert collection.worst_result.metrics[OptimizationMetric.TOTAL_RETURN] == 0.10

    def test_optimization_results_get_completed(self):
        """Test getting only completed results."""
        results = [
            self._create_test_result(
                OptimizationMetric.TOTAL_RETURN, 0.10, OptimizationResultStatus.PENDING
            ),
            self._create_test_result(
                OptimizationMetric.TOTAL_RETURN, 0.20, OptimizationResultStatus.COMPLETED
            ),
            self._create_test_result(
                OptimizationMetric.TOTAL_RETURN, 0.15, OptimizationResultStatus.FAILED
            ),
        ]

        collection = OptimizationResults(config_id=uuid4(), results=results)
        completed = collection.get_completed_results()

        assert len(completed) == 1
        assert completed[0].status == OptimizationResultStatus.COMPLETED

    def test_optimization_results_metric_statistics(self):
        """Test getting metric statistics."""
        results = [
            self._create_test_result(
                OptimizationMetric.TOTAL_RETURN, 0.10, OptimizationResultStatus.COMPLETED
            ),
            self._create_test_result(
                OptimizationMetric.TOTAL_RETURN, 0.20, OptimizationResultStatus.COMPLETED
            ),
            self._create_test_result(
                OptimizationMetric.TOTAL_RETURN, 0.15, OptimizationResultStatus.COMPLETED
            ),
        ]

        collection = OptimizationResults(config_id=uuid4(), results=results)
        stats = collection.get_metric_statistics(OptimizationMetric.TOTAL_RETURN)

        assert stats["min"] == 0.10
        assert stats["max"] == 0.20
        assert stats["mean"] == 0.15
        assert stats["count"] == 3

    def _create_test_result(
        self,
        metric: OptimizationMetric,
        value: float,
        status: OptimizationResultStatus = OptimizationResultStatus.COMPLETED,
    ) -> OptimizationResult:
        """Helper to create a test result."""
        combination = ParameterCombination(
            parameters={"trigger_threshold": 0.02},
            combination_id=f"test_{value}",
            created_at=datetime.utcnow(),
        )

        result = OptimizationResult(
            id=uuid4(),
            config_id=uuid4(),
            parameter_combination=combination,
            metrics={metric: value},
            status=status,
        )

        if status == OptimizationResultStatus.COMPLETED:
            result.mark_completed()
        elif status == OptimizationResultStatus.FAILED:
            result.mark_failed("Test error")

        return result


class TestOptimizationConfig:
    def test_optimization_config_creation(self):
        """Test creating an optimization configuration."""
        config_id = uuid4()
        created_by = uuid4()
        now = datetime.utcnow()

        # Create parameter ranges
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

        # Create optimization criteria
        criteria = OptimizationCriteria(
            primary_metric=OptimizationMetric.TOTAL_RETURN,
            secondary_metrics=[OptimizationMetric.SHARPE_RATIO],
            constraints=[],
            weights={
                OptimizationMetric.TOTAL_RETURN: 1.0,
                OptimizationMetric.SHARPE_RATIO: 0.5,
            },
        )

        config = OptimizationConfig(
            id=config_id,
            name="Test Config",
            ticker="AAPL",
            start_date=now,
            end_date=datetime(2026, 1, 1),
            parameter_ranges=param_ranges,
            optimization_criteria=criteria,
            status=OptimizationStatus.DRAFT,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

        assert config.id == config_id
        assert config.name == "Test Config"
        assert config.ticker == "AAPL"
        assert config.status == OptimizationStatus.DRAFT
        assert config.created_by == created_by

    def test_optimization_config_calculate_total_combinations(self):
        """Test calculating total parameter combinations."""
        config = self._create_test_config()

        # With trigger_threshold: 0.01 to 0.05 step 0.01 = 5 values
        # With rebalance_ratio: 1.0 to 3.0 step 0.5 = 5 values
        # Total = 5 * 5 = 25 combinations
        assert config.calculate_total_combinations() == 25

    def test_optimization_config_calculate_total_combinations_with_max_limit(self):
        """Test calculating total combinations with max limit."""
        config = self._create_test_config()
        config.max_combinations = 10

        # Should be limited to 10 even though 25 are possible
        assert config.calculate_total_combinations() == 10

    def test_optimization_config_status_checks(self):
        """Test status checking methods."""
        config = self._create_test_config()

        # Draft status
        assert not config.is_running()
        assert not config.is_completed()
        assert config.can_start()

        # Running status
        config.status = OptimizationStatus.RUNNING
        assert config.is_running()
        assert not config.is_completed()
        assert not config.can_start()

        # Completed status
        config.status = OptimizationStatus.COMPLETED
        assert not config.is_running()
        assert config.is_completed()
        assert not config.can_start()

    def test_optimization_config_validation_start_after_end_date(self):
        """Test validation fails when start date is after end date."""
        with pytest.raises(ValueError, match="Start date must be before end date"):
            OptimizationConfig(
                id=uuid4(),
                name="Test Config",
                ticker="AAPL",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2024, 1, 1),  # End before start
                parameter_ranges={},
                optimization_criteria=self._create_test_criteria(),
                status=OptimizationStatus.DRAFT,
                created_by=uuid4(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

    def test_optimization_config_validation_empty_parameter_ranges(self):
        """Test validation fails with empty parameter ranges."""
        with pytest.raises(ValueError, match="At least one parameter range must be specified"):
            OptimizationConfig(
                id=uuid4(),
                name="Test Config",
                ticker="AAPL",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2025, 1, 1),
                parameter_ranges={},  # Empty ranges
                optimization_criteria=self._create_test_criteria(),
                status=OptimizationStatus.DRAFT,
                created_by=uuid4(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
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
            ),
            "rebalance_ratio": ParameterRange(
                min_value=1.0,
                max_value=3.0,
                step_size=0.5,
                parameter_type=ParameterType.FLOAT,
                name="rebalance_ratio",
                description="Ratio for rebalancing trades",
            ),
        }

        return OptimizationConfig(
            id=uuid4(),
            name="Test Config",
            ticker="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2025, 1, 1),
            parameter_ranges=param_ranges,
            optimization_criteria=self._create_test_criteria(),
            status=OptimizationStatus.DRAFT,
            created_by=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def _create_test_criteria(self) -> OptimizationCriteria:
        """Helper to create test optimization criteria."""
        return OptimizationCriteria(
            primary_metric=OptimizationMetric.TOTAL_RETURN,
            secondary_metrics=[OptimizationMetric.SHARPE_RATIO],
            constraints=[],
            weights={
                OptimizationMetric.TOTAL_RETURN: 1.0,
                OptimizationMetric.SHARPE_RATIO: 0.5,
            },
        )

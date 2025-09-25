# =========================
# backend/tests/unit/domain/test_optimization_criteria.py
# =========================

import pytest
from domain.value_objects.optimization_criteria import (
    OptimizationCriteria,
    OptimizationMetric,
    Constraint,
    ConstraintType,
)


class TestOptimizationCriteria:
    def test_optimization_criteria_creation(self):
        """Test creating optimization criteria."""
        criteria = OptimizationCriteria(
            primary_metric=OptimizationMetric.TOTAL_RETURN,
            secondary_metrics=[OptimizationMetric.SHARPE_RATIO, OptimizationMetric.MAX_DRAWDOWN],
            constraints=[],
            weights={
                OptimizationMetric.TOTAL_RETURN: 1.0,
                OptimizationMetric.SHARPE_RATIO: 0.5,
                OptimizationMetric.MAX_DRAWDOWN: 0.3,
            },
        )

        assert criteria.primary_metric == OptimizationMetric.TOTAL_RETURN
        assert OptimizationMetric.SHARPE_RATIO in criteria.secondary_metrics
        assert OptimizationMetric.MAX_DRAWDOWN in criteria.secondary_metrics
        assert len(criteria.constraints) == 0
        assert criteria.weights[OptimizationMetric.TOTAL_RETURN] == 1.0

    def test_optimization_criteria_validation_requires_secondary_metrics(self):
        """Test validation fails without secondary metrics."""
        with pytest.raises(ValueError, match="At least one secondary metric must be specified"):
            OptimizationCriteria(
                primary_metric=OptimizationMetric.TOTAL_RETURN,
                secondary_metrics=[],  # Empty secondary metrics
                constraints=[],
                weights={OptimizationMetric.TOTAL_RETURN: 1.0},
            )

    def test_optimization_criteria_validation_primary_not_in_secondary(self):
        """Test validation fails when primary metric is in secondary metrics."""
        with pytest.raises(ValueError, match="Primary metric cannot be in secondary metrics"):
            OptimizationCriteria(
                primary_metric=OptimizationMetric.TOTAL_RETURN,
                secondary_metrics=[OptimizationMetric.TOTAL_RETURN],  # Primary in secondary
                constraints=[],
                weights={
                    OptimizationMetric.TOTAL_RETURN: 1.0,
                },
            )

    def test_optimization_criteria_validation_requires_weights_for_all_metrics(self):
        """Test validation fails when weights are missing for metrics."""
        with pytest.raises(
            ValueError, match="Weight not specified for metric: OptimizationMetric.SHARPE_RATIO"
        ):
            OptimizationCriteria(
                primary_metric=OptimizationMetric.TOTAL_RETURN,
                secondary_metrics=[OptimizationMetric.SHARPE_RATIO],
                constraints=[],
                weights={OptimizationMetric.TOTAL_RETURN: 1.0},  # Missing Sharpe ratio weight
            )

    def test_optimization_criteria_validation_negative_weights(self):
        """Test validation fails with negative weights."""
        with pytest.raises(
            ValueError, match="Weight for OptimizationMetric.TOTAL_RETURN must be non-negative"
        ):
            OptimizationCriteria(
                primary_metric=OptimizationMetric.TOTAL_RETURN,
                secondary_metrics=[OptimizationMetric.SHARPE_RATIO],
                constraints=[],
                weights={
                    OptimizationMetric.TOTAL_RETURN: -1.0,  # Negative weight
                    OptimizationMetric.SHARPE_RATIO: 0.5,
                },
            )

    def test_optimization_criteria_validation_extra_weights(self):
        """Test validation fails with weights for unknown metrics."""
        with pytest.raises(
            ValueError, match="Weight specified for unknown metric: OptimizationMetric.VOLATILITY"
        ):
            OptimizationCriteria(
                primary_metric=OptimizationMetric.TOTAL_RETURN,
                secondary_metrics=[OptimizationMetric.SHARPE_RATIO],
                constraints=[],
                weights={
                    OptimizationMetric.TOTAL_RETURN: 1.0,
                    OptimizationMetric.SHARPE_RATIO: 0.5,
                    OptimizationMetric.VOLATILITY: 0.3,  # Extra weight not in metrics
                },
            )

    def test_optimization_criteria_get_all_metrics(self):
        """Test getting all metrics."""
        criteria = self._create_test_criteria()
        all_metrics = criteria.get_all_metrics()

        assert OptimizationMetric.TOTAL_RETURN in all_metrics
        assert OptimizationMetric.SHARPE_RATIO in all_metrics
        assert len(all_metrics) == 2

    def test_optimization_criteria_get_metric_weight(self):
        """Test getting metric weights."""
        criteria = self._create_test_criteria()

        assert criteria.get_metric_weight(OptimizationMetric.TOTAL_RETURN) == 1.0
        assert criteria.get_metric_weight(OptimizationMetric.SHARPE_RATIO) == 0.5
        assert criteria.get_metric_weight(OptimizationMetric.VOLATILITY) == 0.0  # Not specified

    def test_optimization_criteria_calculate_score(self):
        """Test calculating optimization score."""
        criteria = self._create_test_criteria()

        metrics = {
            OptimizationMetric.TOTAL_RETURN: 0.15,
            OptimizationMetric.SHARPE_RATIO: 1.2,
        }

        score = criteria.calculate_score(metrics)

        # Score = (0.15 * 1.0) + (1.2 * 0.5) = 0.15 + 0.6 = 0.75
        assert score == 0.75

    def test_optimization_criteria_calculate_score_with_minimize(self):
        """Test calculating score with minimize flag."""
        criteria = OptimizationCriteria(
            primary_metric=OptimizationMetric.MAX_DRAWDOWN,
            secondary_metrics=[OptimizationMetric.SHARPE_RATIO],
            constraints=[],
            weights={
                OptimizationMetric.MAX_DRAWDOWN: 1.0,
                OptimizationMetric.SHARPE_RATIO: 0.5,
            },
            minimize=True,  # Minimize drawdown
        )

        metrics = {
            OptimizationMetric.MAX_DRAWDOWN: -0.10,  # 10% drawdown
            OptimizationMetric.SHARPE_RATIO: 1.2,
        }

        score = criteria.calculate_score(metrics)

        # Score = (-(-0.10) * 1.0) + (1.2 * 0.5) = (0.10 * 1.0) + (1.2 * 0.5) = 0.10 + 0.6 = 0.7
        # Note: only primary metric (drawdown) is negated because minimize=True
        assert score == 0.7

    def test_optimization_criteria_calculate_score_with_constraints(self):
        """Test calculating score with constraint penalties."""
        constraint = Constraint(
            metric=OptimizationMetric.SHARPE_RATIO,
            constraint_type=ConstraintType.MIN_VALUE,
            value=1.0,
            weight=2.0,  # High penalty weight
        )

        criteria = OptimizationCriteria(
            primary_metric=OptimizationMetric.TOTAL_RETURN,
            secondary_metrics=[OptimizationMetric.SHARPE_RATIO],
            constraints=[constraint],
            weights={
                OptimizationMetric.TOTAL_RETURN: 1.0,
                OptimizationMetric.SHARPE_RATIO: 0.5,
            },
        )

        # Sharpe ratio below constraint (0.5 < 1.0) should get penalty
        metrics = {
            OptimizationMetric.TOTAL_RETURN: 0.15,
            OptimizationMetric.SHARPE_RATIO: 0.5,  # Below constraint
        }

        score = criteria.calculate_score(metrics)

        # Score = (0.15 * 1.0) + ((0.5 - 2.0) * 0.5) = 0.15 + (-1.5 * 0.5) = 0.15 - 0.75 = -0.6
        assert score == -0.6

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


class TestConstraint:
    def test_constraint_creation(self):
        """Test creating a constraint."""
        constraint = Constraint(
            metric=OptimizationMetric.SHARPE_RATIO,
            constraint_type=ConstraintType.MIN_VALUE,
            value=1.0,
            weight=2.0,
            description="Sharpe ratio must be at least 1.0",
        )

        assert constraint.metric == OptimizationMetric.SHARPE_RATIO
        assert constraint.constraint_type == ConstraintType.MIN_VALUE
        assert constraint.value == 1.0
        assert constraint.weight == 2.0
        assert constraint.description == "Sharpe ratio must be at least 1.0"

    def test_constraint_validation_negative_weight(self):
        """Test validation fails with negative weight."""
        with pytest.raises(ValueError, match="Constraint weight must be non-negative"):
            Constraint(
                metric=OptimizationMetric.SHARPE_RATIO,
                constraint_type=ConstraintType.MIN_VALUE,
                value=1.0,
                weight=-1.0,  # Negative weight
            )

    def test_constraint_validation_range_constraints_require_tuple(self):
        """Test validation fails for range constraints without tuple values."""
        with pytest.raises(
            ValueError, match="Range constraints must have a tuple of \\(min, max\\) values"
        ):
            Constraint(
                metric=OptimizationMetric.SHARPE_RATIO,
                constraint_type=ConstraintType.IN_RANGE,
                value=1.0,  # Should be (min, max) tuple
            )

    def test_constraint_check_min_value(self):
        """Test checking minimum value constraint."""
        constraint = Constraint(
            metric=OptimizationMetric.SHARPE_RATIO,
            constraint_type=ConstraintType.MIN_VALUE,
            value=1.0,
        )

        criteria = self._create_test_criteria()

        # Test constraint checking logic
        assert criteria._check_constraint(constraint, 1.5)  # Above minimum
        assert criteria._check_constraint(constraint, 1.0)  # At minimum
        assert not criteria._check_constraint(constraint, 0.5)  # Below minimum

    def test_constraint_check_max_value(self):
        """Test checking maximum value constraint."""
        constraint = Constraint(
            metric=OptimizationMetric.MAX_DRAWDOWN,
            constraint_type=ConstraintType.MAX_VALUE,
            value=-0.05,  # Max 5% drawdown
        )

        criteria = self._create_test_criteria()

        assert not criteria._check_constraint(
            constraint, -0.03
        )  # Above maximum (less negative) - fails constraint
        assert criteria._check_constraint(constraint, -0.05)  # At maximum - passes constraint
        assert criteria._check_constraint(
            constraint, -0.10
        )  # Below maximum (more negative) - passes constraint

    def test_constraint_check_equal(self):
        """Test checking equality constraint."""
        constraint = Constraint(
            metric=OptimizationMetric.TRADE_COUNT,
            constraint_type=ConstraintType.EQUAL,
            value=50.0,
        )

        criteria = self._create_test_criteria()

        assert criteria._check_constraint(constraint, 50.0)  # Equal
        assert criteria._check_constraint(constraint, 50.000001)  # Within tolerance
        assert not criteria._check_constraint(constraint, 51.0)  # Not equal

    def test_constraint_check_in_range(self):
        """Test checking in-range constraint."""
        constraint = Constraint(
            metric=OptimizationMetric.TRADE_COUNT,
            constraint_type=ConstraintType.IN_RANGE,
            value=(10, 100),  # Between 10 and 100 trades
        )

        criteria = self._create_test_criteria()

        assert criteria._check_constraint(constraint, 50)  # In range
        assert criteria._check_constraint(constraint, 10)  # At minimum
        assert criteria._check_constraint(constraint, 100)  # At maximum
        assert not criteria._check_constraint(constraint, 5)  # Below range
        assert not criteria._check_constraint(constraint, 150)  # Above range

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

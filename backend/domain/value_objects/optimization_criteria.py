# =========================
# backend/domain/value_objects/optimization_criteria.py
# =========================

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class OptimizationMetric(Enum):
    """Available optimization metrics."""

    TOTAL_RETURN = "total_return"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    VOLATILITY = "volatility"
    CALMAR_RATIO = "calmar_ratio"
    SORTINO_RATIO = "sortino_ratio"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    TRADE_COUNT = "trade_count"
    AVG_TRADE_DURATION = "avg_trade_duration"


class ConstraintType(Enum):
    """Types of constraints that can be applied."""

    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    IN_RANGE = "in_range"
    OUT_OF_RANGE = "out_of_range"


@dataclass(frozen=True)
class Constraint:
    """A constraint to be applied during optimization."""

    metric: OptimizationMetric
    constraint_type: ConstraintType
    value: float
    weight: float = 1.0
    description: str = ""

    def __post_init__(self):
        """Validate the constraint after initialization."""
        if self.weight < 0:
            raise ValueError("Constraint weight must be non-negative")

        if self.constraint_type in [ConstraintType.IN_RANGE, ConstraintType.OUT_OF_RANGE]:
            if not isinstance(self.value, (list, tuple)) or len(self.value) != 2:
                raise ValueError("Range constraints must have a tuple of (min, max) values")


@dataclass(frozen=True)
class OptimizationCriteria:
    """Criteria for evaluating optimization results."""

    primary_metric: OptimizationMetric
    secondary_metrics: List[OptimizationMetric]
    constraints: List[Constraint]
    weights: Dict[OptimizationMetric, float]
    minimize: bool = False
    description: str = ""

    def __post_init__(self):
        """Validate the optimization criteria after initialization."""
        if self.primary_metric in self.secondary_metrics:
            raise ValueError("Primary metric cannot be in secondary metrics")

        # Validate weights
        all_metrics = [self.primary_metric] + self.secondary_metrics
        for metric in all_metrics:
            if metric not in self.weights:
                raise ValueError(f"Weight not specified for metric: {metric}")

            if self.weights[metric] < 0:
                raise ValueError(f"Weight for {metric} must be non-negative")

        # Check for extra weights
        for metric in self.weights:
            if metric not in all_metrics:
                raise ValueError(f"Weight specified for unknown metric: {metric}")

        # Validate constraints
        for constraint in self.constraints:
            if constraint.metric not in all_metrics:
                raise ValueError(
                    f"Constraint metric {constraint.metric} not in optimization metrics"
                )

    def get_all_metrics(self) -> List[OptimizationMetric]:
        """Get all metrics used in this optimization."""
        return [self.primary_metric] + self.secondary_metrics

    def get_metric_weight(self, metric: OptimizationMetric) -> float:
        """Get the weight for a specific metric."""
        return self.weights.get(metric, 0.0)

    def get_constraints_for_metric(self, metric: OptimizationMetric) -> List[Constraint]:
        """Get all constraints for a specific metric."""
        return [c for c in self.constraints if c.metric == metric]

    def calculate_score(self, metrics: Dict[OptimizationMetric, float]) -> float:
        """Calculate the overall optimization score."""
        score = 0.0

        for metric in self.get_all_metrics():
            if metric not in metrics:
                continue

            value = metrics[metric]
            weight = self.get_metric_weight(metric)

            # Apply constraints
            constraints = self.get_constraints_for_metric(metric)
            constraint_penalty = 0.0

            for constraint in constraints:
                if not self._check_constraint(constraint, value):
                    constraint_penalty += constraint.weight

            # Apply weight and direction
            if self.minimize and metric == self.primary_metric:
                value = -value

            score += (value - constraint_penalty) * weight

        return score

    def _check_constraint(self, constraint: Constraint, value: float) -> bool:
        """Check if a value satisfies a constraint."""
        if constraint.constraint_type == ConstraintType.MIN_VALUE:
            return value >= constraint.value
        elif constraint.constraint_type == ConstraintType.MAX_VALUE:
            return value <= constraint.value
        elif constraint.constraint_type == ConstraintType.EQUAL:
            return abs(value - constraint.value) < 1e-6
        elif constraint.constraint_type == ConstraintType.NOT_EQUAL:
            return abs(value - constraint.value) >= 1e-6
        elif constraint.constraint_type == ConstraintType.IN_RANGE:
            min_val, max_val = constraint.value
            return min_val <= value <= max_val
        elif constraint.constraint_type == ConstraintType.OUT_OF_RANGE:
            min_val, max_val = constraint.value
            return value < min_val or value > max_val

        return True

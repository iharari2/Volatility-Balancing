# =========================
# backend/domain/entities/optimization_result.py
# =========================

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from enum import Enum

from domain.value_objects.optimization_criteria import OptimizationMetric


class OptimizationResultStatus(Enum):
    """Status of an optimization result."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ParameterCombination:
    """A specific combination of parameters for optimization."""

    parameters: Dict[str, Any]
    combination_id: str
    created_at: datetime

    def __post_init__(self):
        """Validate the parameter combination."""
        if not self.parameters:
            raise ValueError("Parameters cannot be empty")

        if not self.combination_id:
            raise ValueError("Combination ID cannot be empty")


@dataclass
class OptimizationResult:
    """Result of a single parameter combination optimization."""

    id: UUID
    config_id: UUID
    parameter_combination: ParameterCombination
    metrics: Dict[OptimizationMetric, float]
    simulation_result: Optional[Dict[str, Any]] = None
    status: OptimizationResultStatus = OptimizationResultStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None

    def __post_init__(self):
        """Validate the optimization result."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()

        # Allow empty metrics for pending results
        if self.status != OptimizationResultStatus.PENDING and not self.metrics:
            raise ValueError("Metrics cannot be empty for non-pending results")

        if self.status == OptimizationResultStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.utcnow()

    def is_completed(self) -> bool:
        """Check if the optimization result is completed."""
        return self.status == OptimizationResultStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if the optimization result failed."""
        return self.status == OptimizationResultStatus.FAILED

    def mark_completed(self, execution_time: Optional[float] = None) -> None:
        """Mark the result as completed."""
        self.status = OptimizationResultStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if execution_time is not None:
            self.execution_time_seconds = execution_time

    def mark_failed(self, error_message: str) -> None:
        """Mark the result as failed."""
        self.status = OptimizationResultStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def get_metric_value(self, metric: OptimizationMetric) -> Optional[float]:
        """Get the value of a specific metric."""
        return self.metrics.get(metric)

    def calculate_score(self, criteria) -> float:
        """Calculate the optimization score based on criteria."""
        return criteria.calculate_score(self.metrics)


@dataclass
class OptimizationResults:
    """Collection of optimization results for analysis."""

    config_id: UUID
    results: List[OptimizationResult]
    best_result: Optional[OptimizationResult] = None
    worst_result: Optional[OptimizationResult] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        """Initialize timestamps and find best/worst results."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

        if self.results:
            self._find_best_and_worst()

    def _find_best_and_worst(self) -> None:
        """Find the best and worst results based on primary metric."""
        if not self.results:
            return

        # For now, use the first metric as the primary metric
        # In practice, this should be based on the optimization criteria
        primary_metric = list(self.results[0].metrics.keys())[0]

        self.best_result = max(
            self.results, key=lambda r: r.metrics.get(primary_metric, float("-inf"))
        )
        self.worst_result = min(
            self.results, key=lambda r: r.metrics.get(primary_metric, float("inf"))
        )

    def get_completed_results(self) -> List[OptimizationResult]:
        """Get only the completed results."""
        return [r for r in self.results if r.is_completed()]

    def get_failed_results(self) -> List[OptimizationResult]:
        """Get only the failed results."""
        return [r for r in self.results if r.is_failed()]

    def get_metric_statistics(self, metric: OptimizationMetric) -> Dict[str, float]:
        """Get statistics for a specific metric."""
        completed_results = self.get_completed_results()
        if not completed_results:
            return {}

        values = [
            r.get_metric_value(metric)
            for r in completed_results
            if r.get_metric_value(metric) is not None
        ]

        if not values:
            return {}

        return {
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "count": len(values),
        }

    def add_result(self, result: OptimizationResult) -> None:
        """Add a new result to the collection."""
        self.results.append(result)
        self.updated_at = datetime.utcnow()
        self._find_best_and_worst()

    def get_results_by_parameter(
        self, parameter_name: str, parameter_value: Any
    ) -> List[OptimizationResult]:
        """Get results filtered by a specific parameter value."""
        return [
            r
            for r in self.results
            if r.parameter_combination.parameters.get(parameter_name) == parameter_value
        ]

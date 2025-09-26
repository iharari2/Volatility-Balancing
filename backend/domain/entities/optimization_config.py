# =========================
# backend/domain/entities/optimization_config.py
# =========================

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import UUID, uuid4
from enum import Enum

from domain.value_objects.parameter_range import ParameterRange
from domain.value_objects.optimization_criteria import OptimizationCriteria


class OptimizationStatus(Enum):
    """Status of an optimization configuration."""

    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OptimizationConfig:
    """Configuration for parameter optimization runs."""

    id: UUID
    name: str
    ticker: str
    start_date: datetime
    end_date: datetime
    parameter_ranges: Dict[str, ParameterRange]
    optimization_criteria: OptimizationCriteria
    status: OptimizationStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    max_combinations: Optional[int] = None
    batch_size: int = 10

    def __post_init__(self):
        """Validate the configuration after initialization."""
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")

        if not self.parameter_ranges:
            raise ValueError("At least one parameter range must be specified")

        if self.max_combinations is not None and self.max_combinations <= 0:
            raise ValueError("Max combinations must be positive")

    def calculate_total_combinations(self) -> int:
        """Calculate the total number of parameter combinations."""
        total = 1
        for param_range in self.parameter_ranges.values():
            steps = int((param_range.max_value - param_range.min_value) / param_range.step_size) + 1
            total *= steps

        if self.max_combinations is not None:
            return min(total, self.max_combinations)

        return total

    def is_running(self) -> bool:
        """Check if the optimization is currently running."""
        return self.status == OptimizationStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if the optimization has completed."""
        return self.status == OptimizationStatus.COMPLETED

    def can_start(self) -> bool:
        """Check if the optimization can be started."""
        return self.status in [OptimizationStatus.DRAFT, OptimizationStatus.FAILED]

    def update_status(self, new_status: OptimizationStatus) -> None:
        """Update the optimization status."""
        if new_status == OptimizationStatus.RUNNING and not self.can_start():
            raise ValueError(f"Cannot start optimization in status: {self.status}")

        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    @classmethod
    def create(
        cls,
        name: str,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        parameter_ranges: Dict[str, ParameterRange],
        optimization_criteria: OptimizationCriteria,
        created_by: UUID,
        description: Optional[str] = None,
        max_combinations: Optional[int] = None,
        batch_size: int = 10,
    ) -> "OptimizationConfig":
        """Create a new optimization configuration."""
        now = datetime.now(timezone.utc)

        return cls(
            id=uuid4(),
            name=name,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            parameter_ranges=parameter_ranges,
            optimization_criteria=optimization_criteria,
            status=OptimizationStatus.DRAFT,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            description=description,
            max_combinations=max_combinations,
            batch_size=batch_size,
        )

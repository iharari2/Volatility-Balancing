# =========================
# backend/domain/entities/simulation_result.py
# =========================

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID, uuid4


@dataclass
class SimulationResult:
    """Result of a simulation run."""

    id: UUID
    ticker: str
    start_date: str
    end_date: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    raw_data: Optional[Dict[str, Any]] = None
    created_at: datetime = None

    def __post_init__(self):
        """Initialize timestamps."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    @classmethod
    def create(
        cls,
        ticker: str,
        start_date: str,
        end_date: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> "SimulationResult":
        """Create a new simulation result."""
        return cls(
            id=uuid4(),
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters,
            metrics=metrics,
            raw_data=raw_data,
        )







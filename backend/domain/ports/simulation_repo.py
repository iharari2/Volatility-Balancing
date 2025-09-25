# =========================
# backend/domain/ports/simulation_repo.py
# =========================

from abc import ABC, abstractmethod
from typing import Dict, Any
from uuid import UUID

from domain.entities.simulation_result import SimulationResult


class SimulationRepo(ABC):
    """Repository interface for simulation results."""

    @abstractmethod
    def save_simulation_result(self, result: SimulationResult) -> None:
        """Save a simulation result."""
        pass

    @abstractmethod
    def get_simulation_result(self, result_id: UUID) -> SimulationResult:
        """Get a simulation result by ID."""
        pass

    @abstractmethod
    def run_simulation(
        self, ticker: str, start_date: str, end_date: str, parameters: Dict[str, Any]
    ) -> SimulationResult:
        """Run a simulation with given parameters."""
        pass







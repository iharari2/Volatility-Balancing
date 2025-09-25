# =========================
# backend/infrastructure/persistence/memory/simulation_repo_mem.py
# =========================

from typing import Dict, Any
from uuid import UUID

from domain.entities.simulation_result import SimulationResult
from domain.ports.simulation_repo import SimulationRepo


class InMemorySimulationRepo(SimulationRepo):
    """In-memory implementation of simulation repository."""

    def __init__(self):
        self._results: Dict[UUID, SimulationResult] = {}

    def save_simulation_result(self, result: SimulationResult) -> None:
        """Save a simulation result."""
        self._results[result.id] = result

    def get_simulation_result(self, result_id: UUID) -> SimulationResult:
        """Get a simulation result by ID."""
        return self._results.get(result_id)

    def run_simulation(
        self, ticker: str, start_date: str, end_date: str, parameters: Dict[str, Any]
    ) -> SimulationResult:
        """Run a simulation with given parameters."""
        # This is a placeholder implementation
        # In a real implementation, this would call the actual simulation use case

        # Mock metrics for now
        metrics = {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.05,
            "volatility": 0.12,
            "calmar_ratio": 3.0,
            "sortino_ratio": 1.5,
            "win_rate": 0.6,
            "profit_factor": 1.8,
            "trade_count": 25,
            "avg_trade_duration": 5.2,
        }

        result = SimulationResult.create(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters,
            metrics=metrics,
        )

        self.save_simulation_result(result)
        return result







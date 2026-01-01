# =========================
# backend/infrastructure/adapters/sim_position_repo_adapter.py
# =========================
"""Adapter implementing ISimulationPositionRepository for simulation position states."""

from application.ports.repos import ISimulationPositionRepository
from domain.value_objects.position_state import PositionState
from decimal import Decimal


class SimPositionRepoAdapter(ISimulationPositionRepository):
    """Adapter that implements ISimulationPositionRepository for simulation positions."""

    def __init__(self, simulation_repo):
        """
        Initialize adapter with simulation repository.

        Args:
            simulation_repo: Simulation repository for storing simulation state
        """
        self.simulation_repo = simulation_repo
        # Store simulation state in memory for now
        self._sim_states: dict[
            str, dict[str, PositionState]
        ] = {}  # {sim_run_id: {position_id: PositionState}}

    def load_sim_position_state(self, simulation_run_id: str, position_id: str) -> PositionState:
        """Load simulation position state."""
        # Check if we have state for this simulation run and position
        if simulation_run_id in self._sim_states:
            if position_id in self._sim_states[simulation_run_id]:
                return self._sim_states[simulation_run_id][position_id]

        # If no state exists, create initial state
        # TODO: Load from simulation repository or use initial position state
        # For now, create a default state
        initial_state = PositionState(
            ticker="UNKNOWN",  # Should be loaded from simulation config
            qty=Decimal("0"),
            cash=Decimal("10000"),  # Default initial cash
            dividend_receivable=Decimal("0"),
            anchor_price=None,
        )

        # Store it
        if simulation_run_id not in self._sim_states:
            self._sim_states[simulation_run_id] = {}
        self._sim_states[simulation_run_id][position_id] = initial_state

        return initial_state

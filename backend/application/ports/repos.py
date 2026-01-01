# =========================
# backend/application/ports/repos.py
# =========================
from abc import ABC, abstractmethod
from typing import Iterable

from domain.value_objects.position_state import PositionState


class IPositionRepository(ABC):
    """Port for position repository operations."""

    @abstractmethod
    def get_active_positions_for_trading(self) -> Iterable[str]:
        """Return identifiers for positions that should be considered in live trading."""
        ...

    @abstractmethod
    def load_position_state(self, position_id: str) -> PositionState:
        """Load position state for a position."""
        ...


class ISimulationPositionRepository(ABC):
    """Port for simulation position repository operations."""

    @abstractmethod
    def load_sim_position_state(self, simulation_run_id: str, position_id: str) -> PositionState:
        """Load simulation position state."""
        ...


class IEventLogger(ABC):
    """Port for event logging."""

    @abstractmethod
    def log_event(self, event_type: str, payload: dict) -> None:
        """Log an event with type and payload."""
        ...

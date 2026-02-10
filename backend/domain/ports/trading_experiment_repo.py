# backend/domain/ports/trading_experiment_repo.py
from typing import Protocol, Optional, List
from domain.entities.trading_experiment import TradingExperiment


class TradingExperimentRepo(Protocol):
    """Repository interface for TradingExperiment entities."""

    def get(self, tenant_id: str, experiment_id: str) -> Optional[TradingExperiment]:
        """Get an experiment by ID, scoped to tenant."""
        ...

    def save(self, experiment: TradingExperiment) -> None:
        """Save (create or update) an experiment."""
        ...

    def delete(self, tenant_id: str, experiment_id: str) -> bool:
        """Delete an experiment by ID. Returns True if deleted."""
        ...

    def list_all(self, tenant_id: str) -> List[TradingExperiment]:
        """List all experiments for a tenant."""
        ...

    def list_by_status(self, tenant_id: str, status: str) -> List[TradingExperiment]:
        """List experiments by status (RUNNING, PAUSED, COMPLETED)."""
        ...

    def clear(self) -> None:
        """Clear all experiments (test helper)."""
        ...

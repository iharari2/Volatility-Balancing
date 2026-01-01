# =========================
# backend/domain/ports/evaluation_timeline_repo.py
# =========================
"""Port for PositionEvaluationTimeline repository operations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class EvaluationTimelineRepo(ABC):
    """Repository for PositionEvaluationTimeline records."""

    @abstractmethod
    def save(self, evaluation_data: Dict[str, Any]) -> str:
        """
        Save an evaluation timeline record.

        Args:
            evaluation_data: Dictionary containing all evaluation fields

        Returns:
            The ID of the saved record
        """
        ...

    @abstractmethod
    def get_by_id(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Get an evaluation record by ID."""
        ...

    @abstractmethod
    def list_by_position(
        self,
        tenant_id: str,
        portfolio_id: str,
        position_id: str,
        mode: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List evaluation records for a position.

        Args:
            tenant_id: Tenant ID
            portfolio_id: Portfolio ID
            position_id: Position ID
            mode: Filter by mode (LIVE, SIMULATION)
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of records to return

        Returns:
            List of evaluation records
        """
        ...

    @abstractmethod
    def list_by_portfolio(
        self,
        tenant_id: str,
        portfolio_id: str,
        mode: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List evaluation records for a portfolio."""
        ...

    @abstractmethod
    def list_by_trace_id(self, trace_id: str) -> List[Dict[str, Any]]:
        """List all evaluation records for a trace_id."""
        ...

    @abstractmethod
    def list_by_simulation_run(
        self,
        simulation_run_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List evaluation records for a simulation run."""
        ...

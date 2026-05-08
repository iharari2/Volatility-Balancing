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
        action_filter: Optional[List[str]] = None,
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
        action_filter: Optional[List[str]] = None,
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

    def list_snapshots_by_resolution(
        self,
        tenant_id: str,
        portfolio_id: str,
        resolution: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        position_id: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return the latest evaluation per (time-bucket, position) pair.

        Default implementation falls back to list_by_portfolio with a high limit.
        Subclasses should override with an efficient DB-level aggregation.
        """
        rows = self.list_by_portfolio(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            mode=mode,
            start_date=start_date,
            end_date=end_date,
            limit=None,
        )
        if position_id:
            rows = [r for r in rows if r.get("position_id") == position_id]
        return rows

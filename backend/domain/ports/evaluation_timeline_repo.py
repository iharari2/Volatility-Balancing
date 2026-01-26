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

    def get_position_snapshot_at(
        self,
        tenant_id: str,
        portfolio_id: str,
        position_id: str,
        as_of: datetime,
        mode: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the position state as of a specific timestamp.

        Returns the most recent evaluation record before or at the given timestamp.

        Args:
            tenant_id: Tenant ID
            portfolio_id: Portfolio ID
            position_id: Position ID
            as_of: The timestamp to query state at
            mode: Filter by mode (LIVE, SIMULATION)

        Returns:
            The evaluation record closest to (but not after) as_of, or None if not found
        """
        # Default implementation using list_by_position
        records = self.list_by_position(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            mode=mode,
            end_date=as_of,
            limit=1,
        )
        return records[0] if records else None

    def get_daily_summaries(
        self,
        tenant_id: str,
        portfolio_id: str,
        position_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        mode: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get daily summary of position/portfolio performance.

        Returns one record per day with:
        - date: The date
        - open_value: First recorded total value of the day
        - close_value: Last recorded total value of the day
        - high_value: Maximum total value during the day
        - low_value: Minimum total value during the day
        - evaluation_count: Number of evaluations that day
        - trade_count: Number of trades executed that day

        Args:
            tenant_id: Tenant ID
            portfolio_id: Portfolio ID
            position_id: Optional position ID (if None, aggregates portfolio)
            start_date: Start date filter
            end_date: End date filter
            mode: Filter by mode (LIVE, SIMULATION)

        Returns:
            List of daily summary records
        """
        # Default implementation - subclasses can override with efficient SQL
        return []

    def get_performance_series(
        self,
        tenant_id: str,
        portfolio_id: str,
        position_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        mode: Optional[str] = None,
        interval: str = "1h",
    ) -> List[Dict[str, Any]]:
        """
        Get time series of portfolio/position value for charting.

        Args:
            tenant_id: Tenant ID
            portfolio_id: Portfolio ID
            position_id: Optional position ID (if None, uses portfolio)
            start_date: Start date filter
            end_date: End date filter
            mode: Filter by mode (LIVE, SIMULATION)
            interval: Time interval - "1h", "4h", "1d"

        Returns:
            List of {timestamp, total_value, stock_value, cash, allocation_pct}
        """
        # Default implementation - subclasses can override with efficient SQL
        return []

# =========================
# backend/domain/ports/position_event_repo.py
# =========================
"""Port for PositionEvent repository operations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class PositionEventRepo(ABC):
    """Repository for PositionEvent records (immutable log)."""

    @abstractmethod
    def save(self, event_data: Dict[str, Any]) -> str:
        """
        Save a position event record (immutable log).

        Args:
            event_data: Dictionary containing all event fields

        Returns:
            The ID of the saved record
        """
        ...

    @abstractmethod
    def get_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get an event record by ID."""
        ...

    @abstractmethod
    def list_by_position(
        self,
        position_id: str,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List event records for a position.

        Args:
            position_id: Position ID
            event_type: Filter by event type (PRICE, TRIGGER, GUARDRAIL, ORDER, TRADE)
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of records to return

        Returns:
            List of event records, ordered by timestamp (newest first)
        """
        ...

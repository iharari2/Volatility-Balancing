# =========================
# backend/domain/ports/position_baseline_repo.py
# =========================
"""Port for PositionBaseline repository operations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class PositionBaselineRepo(ABC):
    """Repository for PositionBaseline records."""

    @abstractmethod
    def save(self, baseline_data: Dict[str, Any]) -> str:
        """
        Save a position baseline record.

        Args:
            baseline_data: Dictionary containing all baseline fields

        Returns:
            The ID of the saved record
        """
        ...

    @abstractmethod
    def get_latest(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest baseline for a position."""
        ...

    @abstractmethod
    def list_by_position(
        self,
        position_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List baseline records for a position, ordered by timestamp (newest first)."""
        ...

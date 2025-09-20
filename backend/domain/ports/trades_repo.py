# =========================
# backend/domain/ports/trades_repo.py
# =========================
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.trade import Trade


class TradesRepo(ABC):
    """Repository interface for trade persistence."""

    @abstractmethod
    def save(self, trade: Trade) -> None:
        """Save a trade to persistent storage."""
        pass

    @abstractmethod
    def get(self, trade_id: str) -> Optional[Trade]:
        """Get a trade by ID."""
        pass

    @abstractmethod
    def list_for_position(self, position_id: str, limit: int = 100) -> List[Trade]:
        """List trades for a position, ordered by execution time (newest first)."""
        pass

    @abstractmethod
    def list_for_order(self, order_id: str) -> List[Trade]:
        """List trades for an order (typically 1 trade per order)."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all trades (test helper)."""
        pass

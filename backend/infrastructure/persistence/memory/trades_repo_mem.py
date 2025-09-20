# =========================
# backend/infrastructure/persistence/memory/trades_repo_mem.py
# =========================
from __future__ import annotations

from typing import Dict, List, Optional

from domain.entities.trade import Trade
from domain.ports.trades_repo import TradesRepo


class InMemoryTradesRepo(TradesRepo):
    def __init__(self) -> None:
        self._items: Dict[str, Trade] = {}
        self._by_position: Dict[str, List[str]] = {}  # position_id -> [trade_ids]
        self._by_order: Dict[str, List[str]] = {}  # order_id -> [trade_ids]

    def save(self, trade: Trade) -> None:
        """Save a trade to memory storage."""
        self._items[trade.id] = trade

        # Update indexes
        if trade.position_id not in self._by_position:
            self._by_position[trade.position_id] = []
        if trade.position_id not in self._by_order:
            self._by_order[trade.order_id] = []

        if trade.id not in self._by_position[trade.position_id]:
            self._by_position[trade.position_id].append(trade.id)
        if trade.id not in self._by_order[trade.order_id]:
            self._by_order[trade.order_id].append(trade.id)

    def get(self, trade_id: str) -> Optional[Trade]:
        """Get a trade by ID."""
        return self._items.get(trade_id)

    def list_for_position(self, position_id: str, limit: int = 100) -> List[Trade]:
        """List trades for a position, ordered by execution time (newest first)."""
        trade_ids = self._by_position.get(position_id, [])
        trades = [self._items[tid] for tid in trade_ids if tid in self._items]
        # Sort by execution time (newest first)
        trades.sort(key=lambda t: t.executed_at, reverse=True)
        return trades[:limit]

    def list_for_order(self, order_id: str) -> List[Trade]:
        """List trades for an order (typically 1 trade per order)."""
        trade_ids = self._by_order.get(order_id, [])
        return [self._items[tid] for tid in trade_ids if tid in self._items]

    def clear(self) -> None:
        """Clear all trades."""
        self._items.clear()
        self._by_position.clear()
        self._by_order.clear()

# =========================
# backend/infrastructure/persistence/memory/positions_repo_mem.py
# =========================
import uuid
from typing import Dict, Optional, List

from domain.entities.position import Position
from domain.ports.positions_repo import PositionsRepo


class InMemoryPositionsRepo(PositionsRepo):
    def __init__(self) -> None:
        # Store positions by (tenant_id, portfolio_id, position_id) tuple
        self._items: Dict[tuple[str, str, str], Position] = {}

    def get(self, tenant_id: str, portfolio_id: str, position_id: str) -> Optional[Position]:
        return self._items.get((tenant_id, portfolio_id, position_id))

    def create(
        self,
        tenant_id: str,
        portfolio_id: str,
        asset_symbol: str,
        qty: float,
        anchor_price: Optional[float] = None,
        avg_cost: Optional[float] = None,
    ) -> Position:
        pid = f"pos_{uuid.uuid4().hex[:8]}"
        pos = Position(
            id=pid,
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            asset_symbol=asset_symbol,
            qty=qty,
            anchor_price=anchor_price,
            avg_cost=avg_cost,
        )
        self._items[(tenant_id, portfolio_id, pid)] = pos
        return pos

    def save(self, position: Position) -> None:
        print(f"DEBUG: Saving position {position.id} with anchor_price={position.anchor_price}")
        self._items[(position.tenant_id, position.portfolio_id, position.id)] = position
        print(
            f"DEBUG: Saved position {position.id}, stored anchor_price={self._items[(position.tenant_id, position.portfolio_id, position.id)].anchor_price}"
        )

    def delete(self, tenant_id: str, portfolio_id: str, position_id: str) -> bool:
        """Delete a position by ID. Returns True if deleted, False if not found."""
        key = (tenant_id, portfolio_id, position_id)
        if key in self._items:
            del self._items[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all positions."""
        self._items.clear()

    def list_all(self, tenant_id: str, portfolio_id: str) -> List[Position]:
        """List all positions for a tenant and portfolio."""
        return [
            pos
            for (t_id, p_id, _), pos in self._items.items()
            if t_id == tenant_id and p_id == portfolio_id
        ]

    def get_by_asset(
        self, tenant_id: str, portfolio_id: str, asset_symbol: str
    ) -> Optional[Position]:
        """Get a position by asset symbol, scoped to tenant and portfolio."""
        for (t_id, p_id, _), pos in self._items.items():
            if t_id == tenant_id and p_id == portfolio_id and pos.asset_symbol == asset_symbol:
                return pos
        return None

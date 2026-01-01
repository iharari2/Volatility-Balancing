# =========================
# backend/domain/entities/portfolio.py
# =========================
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Portfolio:
    """Domain entity representing a portfolio - a collection of positions."""

    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    user_id: str = "default"  # For multi-user support in the future
    type: str = "LIVE"  # LIVE/SIM/SANDBOX
    trading_state: str = "NOT_CONFIGURED"  # READY/RUNNING/PAUSED/ERROR/NOT_CONFIGURED
    trading_hours_policy: str = "OPEN_ONLY"  # OPEN_ONLY/OPEN_PLUS_AFTER_HOURS

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        trading_state: Optional[str] = None,
        trading_hours_policy: Optional[str] = None,
    ) -> None:
        """Update portfolio metadata."""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if trading_state is not None:
            self.trading_state = trading_state
        if trading_hours_policy is not None:
            self.trading_hours_policy = trading_hours_policy
        self.updated_at = datetime.now(timezone.utc)

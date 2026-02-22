from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class User:
    id: str
    tenant_id: str
    email: str
    hashed_password: str
    display_name: str = ""
    role: str = "owner"  # "owner" | "member"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

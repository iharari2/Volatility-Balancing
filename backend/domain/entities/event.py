# =========================
# backend/domain/entities/event.py
# =========================

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class Event:
    id: str
    position_id: str
    type: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    message: str
    ts: datetime

    def __hash__(self):
        return hash((self.id, self.position_id, self.type, self.ts))

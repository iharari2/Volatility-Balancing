# =========================
# backend/domain/value_objects/triggers.py
# =========================
from dataclasses import dataclass


@dataclass
class TriggerRule:
    threshold_pct: float = 0.03  # move that triggers a trade
    step_pct: float = 0.05       # trade size when triggered

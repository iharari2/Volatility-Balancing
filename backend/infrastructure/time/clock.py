# =========================
# backend/infrastructure/time/clock.py
# =========================

from datetime import datetime, timezone

class Clock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

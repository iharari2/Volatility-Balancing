# =========================
# backend/infrastructure/logging/json_event_logger.py
# =========================
"""JSON file-based event logger implementation."""

from __future__ import annotations
import json
from pathlib import Path
from threading import Lock
from application.events import EventRecord
from application.ports.event_logger import IEventLogger


class JsonFileEventLogger(IEventLogger):
    """Event logger that writes events to a JSONL (JSON Lines) file."""

    def __init__(self, log_file: str | Path):
        """
        Initialize JSON file event logger.

        Args:
            log_file: Path to the log file (will be created if it doesn't exist)
        """
        self._path = Path(log_file)
        self._lock = Lock()
        # Ensure parent directory exists
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: EventRecord) -> None:
        """Log an event record to the JSON file."""
        serializable = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "created_at": event.created_at.isoformat(),
            "tenant_id": event.tenant_id,
            "portfolio_id": event.portfolio_id,
            "asset_id": event.asset_id,
            "trace_id": event.trace_id,
            "parent_event_id": event.parent_event_id,
            "source": event.source,
            "payload": event.payload,
            "version": event.version,
        }
        line = json.dumps(serializable, ensure_ascii=False)

        with self._lock:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

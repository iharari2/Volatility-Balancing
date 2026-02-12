from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


class StructuredJsonFormatter(logging.Formatter):
    """JSON formatter for CloudWatch-compatible structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        for key in ("position_id", "trace_id", "source", "order_id", "alert_id"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def configure_structured_logging(level: str = "INFO") -> None:
    """Replace root logger handlers with structured JSON formatter.

    Only activated when STRUCTURED_LOGGING=true env var is set.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    root.addHandler(handler)

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class AlertSeverity(str, Enum):
    warning = "warning"
    critical = "critical"


class AlertCondition(str, Enum):
    worker_stopped = "worker_stopped"
    no_evaluations = "no_evaluations"
    order_rejected = "order_rejected"
    guardrail_skip_threshold = "guardrail_skip_threshold"
    price_data_stale = "price_data_stale"
    broker_unreachable = "broker_unreachable"


class AlertStatus(str, Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"


@dataclass
class Alert:
    id: str
    condition: AlertCondition
    severity: AlertSeverity
    status: AlertStatus
    title: str
    detail: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def new(
        condition: AlertCondition,
        severity: AlertSeverity,
        title: str,
        detail: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        return Alert(
            id=str(uuid.uuid4()),
            condition=condition,
            severity=severity,
            status=AlertStatus.active,
            title=title,
            detail=detail,
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

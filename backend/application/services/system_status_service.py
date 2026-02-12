from __future__ import annotations

import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from domain.ports.alert_repo import AlertRepo
from infrastructure.time.clock import Clock

logger = logging.getLogger(__name__)

_start_time = time.monotonic()


class SystemStatusService:
    def __init__(
        self,
        alert_repo: AlertRepo,
        clock: Clock,
    ):
        self._alert_repo = alert_repo
        self._clock = clock

    def get_health(
        self,
        worker_running: bool = False,
        worker_enabled: bool = False,
        broker_reachable: bool = True,
    ) -> Dict[str, Any]:
        components: Dict[str, str] = {}

        # Worker check
        if worker_enabled and worker_running:
            components["trading_worker"] = "healthy"
        elif not worker_enabled:
            components["trading_worker"] = "disabled"
        else:
            components["trading_worker"] = "unhealthy"

        # Broker check
        components["broker"] = "healthy" if broker_reachable else "unhealthy"

        # Determine overall status
        values = list(components.values())
        if "unhealthy" in values:
            status = "unhealthy"
        elif "disabled" in values or "degraded" in values:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "components": components,
            "uptime_seconds": round(time.monotonic() - _start_time, 1),
        }

    def get_full_status(
        self,
        worker_running: bool = False,
        worker_enabled: bool = False,
        worker_interval: int = 60,
        last_evaluation_time: Optional[datetime] = None,
        broker_reachable: bool = True,
    ) -> Dict[str, Any]:
        health = self.get_health(
            worker_running=worker_running,
            worker_enabled=worker_enabled,
            broker_reachable=broker_reachable,
        )

        active_alerts = self._alert_repo.list_active()
        alert_dicts: List[Dict[str, Any]] = []
        for a in active_alerts:
            alert_dicts.append({
                "id": a.id,
                "condition": a.condition.value,
                "severity": a.severity.value,
                "status": a.status.value,
                "title": a.title,
                "detail": a.detail,
                "created_at": a.created_at.isoformat(),
            })

        return {
            **health,
            "active_alerts": alert_dicts,
            "active_alert_count": len(alert_dicts),
            "worker": {
                "running": worker_running,
                "enabled": worker_enabled,
                "interval_seconds": worker_interval,
            },
            "last_evaluation_time": last_evaluation_time.isoformat() if last_evaluation_time else None,
            "timestamp": self._clock.now().isoformat(),
        }

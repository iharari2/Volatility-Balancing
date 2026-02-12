from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.entities.alert import Alert, AlertCondition, AlertSeverity
from infrastructure.persistence.memory.alert_repo_mem import InMemoryAlertRepo
from infrastructure.time.clock import Clock
from application.services.system_status_service import SystemStatusService


class FakeClock(Clock):
    def __init__(self, now: datetime):
        self._now = now

    def now(self) -> datetime:
        return self._now


@pytest.fixture
def repo() -> InMemoryAlertRepo:
    return InMemoryAlertRepo()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(datetime(2026, 2, 12, 15, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def svc(repo, clock) -> SystemStatusService:
    return SystemStatusService(alert_repo=repo, clock=clock)


def test_health_returns_components_and_uptime(svc):
    result = svc.get_health(worker_running=True, worker_enabled=True)
    assert result["status"] == "healthy"
    assert "trading_worker" in result["components"]
    assert "uptime_seconds" in result


def test_degraded_when_worker_disabled(svc):
    result = svc.get_health(worker_running=False, worker_enabled=False)
    assert result["status"] == "degraded"
    assert result["components"]["trading_worker"] == "disabled"


def test_full_status_includes_active_alerts(svc, repo):
    alert = Alert.new(
        condition=AlertCondition.worker_stopped,
        severity=AlertSeverity.critical,
        title="Worker down",
        detail="Worker is down.",
    )
    repo.save(alert)

    result = svc.get_full_status(worker_running=False, worker_enabled=True)
    assert result["active_alert_count"] == 1
    assert result["active_alerts"][0]["condition"] == "worker_stopped"
    assert "worker" in result
    assert "timestamp" in result

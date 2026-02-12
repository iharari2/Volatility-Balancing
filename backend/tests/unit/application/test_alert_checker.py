from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from domain.entities.alert import AlertCondition, AlertSeverity
from infrastructure.persistence.memory.alert_repo_mem import InMemoryAlertRepo
from infrastructure.time.clock import Clock
from application.services.alert_checker import AlertChecker


class FakeClock(Clock):
    def __init__(self, now: datetime):
        self._now = now

    def now(self) -> datetime:
        return self._now


@pytest.fixture
def repo() -> InMemoryAlertRepo:
    return InMemoryAlertRepo()


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 2, 12, 15, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def clock(now) -> FakeClock:
    return FakeClock(now)


@pytest.fixture
def checker(repo, clock) -> AlertChecker:
    return AlertChecker(
        alert_repo=repo,
        clock=clock,
        no_eval_minutes=10,
        guardrail_skip_threshold=5,
        price_stale_minutes=5,
    )


def test_worker_stopped_creates_alert(checker, repo):
    alerts = checker.run_all_checks(
        worker_running=False,
        worker_enabled=True,
        last_evaluation_time=None,
        is_market_hours=False,
    )
    worker_alerts = [a for a in alerts if a.condition == AlertCondition.worker_stopped]
    assert len(worker_alerts) == 1
    assert worker_alerts[0].severity == AlertSeverity.critical
    assert repo.find_active_by_condition(AlertCondition.worker_stopped) is not None


def test_worker_stopped_deduplicates(checker, repo):
    checker.run_all_checks(
        worker_running=False, worker_enabled=True,
        last_evaluation_time=None, is_market_hours=False,
    )
    alerts = checker.run_all_checks(
        worker_running=False, worker_enabled=True,
        last_evaluation_time=None, is_market_hours=False,
    )
    worker_alerts = [a for a in alerts if a.condition == AlertCondition.worker_stopped]
    assert len(worker_alerts) == 0


def test_worker_stopped_auto_resolves(checker, repo):
    checker.run_all_checks(
        worker_running=False, worker_enabled=True,
        last_evaluation_time=None, is_market_hours=False,
    )
    assert repo.find_active_by_condition(AlertCondition.worker_stopped) is not None

    checker.run_all_checks(
        worker_running=True, worker_enabled=True,
        last_evaluation_time=None, is_market_hours=False,
    )
    assert repo.find_active_by_condition(AlertCondition.worker_stopped) is None


def test_no_evaluations_fires_during_market_hours(checker, repo, now):
    alerts = checker.run_all_checks(
        worker_running=True, worker_enabled=True,
        last_evaluation_time=now - timedelta(minutes=15),
        is_market_hours=True,
    )
    eval_alerts = [a for a in alerts if a.condition == AlertCondition.no_evaluations]
    assert len(eval_alerts) == 1


def test_no_evaluations_ignores_outside_hours(checker, repo, now):
    alerts = checker.run_all_checks(
        worker_running=True, worker_enabled=True,
        last_evaluation_time=now - timedelta(minutes=15),
        is_market_hours=False,
    )
    eval_alerts = [a for a in alerts if a.condition == AlertCondition.no_evaluations]
    assert len(eval_alerts) == 0


def test_no_evaluations_resolves_when_recent(checker, repo, now):
    # Fire alert first
    checker.run_all_checks(
        worker_running=True, worker_enabled=True,
        last_evaluation_time=now - timedelta(minutes=15),
        is_market_hours=True,
    )
    assert repo.find_active_by_condition(AlertCondition.no_evaluations) is not None

    # Resolve when recent evaluation
    checker.run_all_checks(
        worker_running=True, worker_enabled=True,
        last_evaluation_time=now - timedelta(minutes=2),
        is_market_hours=True,
    )
    assert repo.find_active_by_condition(AlertCondition.no_evaluations) is None


def test_order_rejections_creates_and_resolves(checker, repo):
    alerts = checker.run_all_checks(
        worker_running=True, worker_enabled=True,
        last_evaluation_time=None, is_market_hours=False,
        recent_order_rejections=3,
    )
    reject_alerts = [a for a in alerts if a.condition == AlertCondition.order_rejected]
    assert len(reject_alerts) == 1

    alerts = checker.run_all_checks(
        worker_running=True, worker_enabled=True,
        last_evaluation_time=None, is_market_hours=False,
        recent_order_rejections=0,
    )
    assert repo.find_active_by_condition(AlertCondition.order_rejected) is None


def test_guardrail_skips_below_threshold_no_alert(checker, repo):
    alerts = checker.run_all_checks(
        worker_running=True, worker_enabled=True,
        last_evaluation_time=None, is_market_hours=False,
        recent_guardrail_skips=3,
    )
    skip_alerts = [a for a in alerts if a.condition == AlertCondition.guardrail_skip_threshold]
    assert len(skip_alerts) == 0


def test_guardrail_skips_at_threshold_creates_alert(checker, repo):
    alerts = checker.run_all_checks(
        worker_running=True, worker_enabled=True,
        last_evaluation_time=None, is_market_hours=False,
        recent_guardrail_skips=5,
    )
    skip_alerts = [a for a in alerts if a.condition == AlertCondition.guardrail_skip_threshold]
    assert len(skip_alerts) == 1


def test_all_ok_returns_zero_alerts(checker, repo, now):
    alerts = checker.run_all_checks(
        worker_running=True,
        worker_enabled=True,
        last_evaluation_time=now - timedelta(minutes=1),
        is_market_hours=True,
        recent_order_rejections=0,
        recent_guardrail_skips=0,
        last_price_update=now - timedelta(minutes=1),
        broker_reachable=True,
    )
    assert len(alerts) == 0

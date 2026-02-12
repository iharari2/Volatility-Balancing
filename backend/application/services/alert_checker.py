from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from domain.entities.alert import Alert, AlertCondition, AlertSeverity, AlertStatus
from domain.ports.alert_repo import AlertRepo
from infrastructure.time.clock import Clock

logger = logging.getLogger(__name__)


class AlertChecker:
    def __init__(
        self,
        alert_repo: AlertRepo,
        clock: Clock,
        no_eval_minutes: int = 10,
        guardrail_skip_threshold: int = 5,
        price_stale_minutes: int = 5,
    ):
        self._repo = alert_repo
        self._clock = clock
        self.no_eval_minutes = no_eval_minutes
        self.guardrail_skip_threshold = guardrail_skip_threshold
        self.price_stale_minutes = price_stale_minutes

    def run_all_checks(
        self,
        worker_running: bool,
        worker_enabled: bool,
        last_evaluation_time: Optional[datetime],
        is_market_hours: bool,
        recent_order_rejections: int = 0,
        recent_guardrail_skips: int = 0,
        last_price_update: Optional[datetime] = None,
        broker_reachable: bool = True,
    ) -> List[Alert]:
        new_alerts: List[Alert] = []

        new_alerts.extend(self._check_worker_stopped(worker_running, worker_enabled))
        new_alerts.extend(self._check_no_evaluations(last_evaluation_time, is_market_hours))
        new_alerts.extend(self._check_order_rejections(recent_order_rejections))
        new_alerts.extend(self._check_guardrail_skips(recent_guardrail_skips))
        new_alerts.extend(self._check_price_data_stale(last_price_update, is_market_hours))
        new_alerts.extend(self._check_broker_unreachable(broker_reachable))

        return new_alerts

    def _check_worker_stopped(self, worker_running: bool, worker_enabled: bool) -> List[Alert]:
        condition = AlertCondition.worker_stopped
        existing = self._repo.find_active_by_condition(condition)

        if not worker_running and worker_enabled:
            if existing:
                return []
            alert = Alert.new(
                condition=condition,
                severity=AlertSeverity.critical,
                title="Trading worker stopped unexpectedly",
                detail="The trading worker is enabled but not running.",
            )
            self._repo.save(alert)
            return [alert]

        if existing and (worker_running or not worker_enabled):
            self._resolve(existing)
        return []

    def _check_no_evaluations(
        self, last_evaluation_time: Optional[datetime], is_market_hours: bool
    ) -> List[Alert]:
        condition = AlertCondition.no_evaluations
        existing = self._repo.find_active_by_condition(condition)

        if not is_market_hours:
            if existing:
                self._resolve(existing)
            return []

        if last_evaluation_time is None:
            if existing:
                return []
            alert = Alert.new(
                condition=condition,
                severity=AlertSeverity.warning,
                title="No evaluations recorded",
                detail="No position evaluations have been recorded during market hours.",
            )
            self._repo.save(alert)
            return [alert]

        now = self._clock.now()
        minutes_since = (now - last_evaluation_time).total_seconds() / 60.0

        if minutes_since > self.no_eval_minutes:
            if existing:
                return []
            alert = Alert.new(
                condition=condition,
                severity=AlertSeverity.warning,
                title="No recent evaluations",
                detail=f"No evaluations in the last {minutes_since:.0f} minutes (threshold: {self.no_eval_minutes}m).",
            )
            self._repo.save(alert)
            return [alert]

        if existing:
            self._resolve(existing)
        return []

    def _check_order_rejections(self, recent_order_rejections: int) -> List[Alert]:
        condition = AlertCondition.order_rejected
        existing = self._repo.find_active_by_condition(condition)

        if recent_order_rejections > 0:
            if existing:
                return []
            alert = Alert.new(
                condition=condition,
                severity=AlertSeverity.warning,
                title="Order rejections detected",
                detail=f"{recent_order_rejections} order(s) rejected recently.",
                metadata={"count": recent_order_rejections},
            )
            self._repo.save(alert)
            return [alert]

        if existing:
            self._resolve(existing)
        return []

    def _check_guardrail_skips(self, recent_guardrail_skips: int) -> List[Alert]:
        condition = AlertCondition.guardrail_skip_threshold
        existing = self._repo.find_active_by_condition(condition)

        if recent_guardrail_skips >= self.guardrail_skip_threshold:
            if existing:
                return []
            alert = Alert.new(
                condition=condition,
                severity=AlertSeverity.warning,
                title="Guardrail skip threshold reached",
                detail=f"{recent_guardrail_skips} guardrail skips (threshold: {self.guardrail_skip_threshold}).",
                metadata={"count": recent_guardrail_skips},
            )
            self._repo.save(alert)
            return [alert]

        if existing:
            self._resolve(existing)
        return []

    def _check_price_data_stale(
        self, last_price_update: Optional[datetime], is_market_hours: bool
    ) -> List[Alert]:
        condition = AlertCondition.price_data_stale
        existing = self._repo.find_active_by_condition(condition)

        if not is_market_hours:
            if existing:
                self._resolve(existing)
            return []

        if last_price_update is None:
            # No price data at all during market hours
            if existing:
                return []
            alert = Alert.new(
                condition=condition,
                severity=AlertSeverity.warning,
                title="No price data available",
                detail="No price data updates recorded during market hours.",
            )
            self._repo.save(alert)
            return [alert]

        now = self._clock.now()
        minutes_since = (now - last_price_update).total_seconds() / 60.0

        if minutes_since > self.price_stale_minutes:
            if existing:
                return []
            alert = Alert.new(
                condition=condition,
                severity=AlertSeverity.warning,
                title="Price data stale",
                detail=f"No price update in {minutes_since:.0f} minutes (threshold: {self.price_stale_minutes}m).",
            )
            self._repo.save(alert)
            return [alert]

        if existing:
            self._resolve(existing)
        return []

    def _check_broker_unreachable(self, broker_reachable: bool) -> List[Alert]:
        condition = AlertCondition.broker_unreachable
        existing = self._repo.find_active_by_condition(condition)

        if not broker_reachable:
            if existing:
                return []
            alert = Alert.new(
                condition=condition,
                severity=AlertSeverity.critical,
                title="Broker unreachable",
                detail="Cannot connect to broker service.",
            )
            self._repo.save(alert)
            return [alert]

        if existing:
            self._resolve(existing)
        return []

    def _resolve(self, alert: Alert) -> None:
        alert.status = AlertStatus.resolved
        alert.resolved_at = self._clock.now()
        self._repo.save(alert)

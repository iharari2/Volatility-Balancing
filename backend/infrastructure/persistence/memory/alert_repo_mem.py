from __future__ import annotations

from typing import Dict, List, Optional

from domain.entities.alert import Alert, AlertCondition, AlertStatus
from domain.ports.alert_repo import AlertRepo


class InMemoryAlertRepo(AlertRepo):
    def __init__(self) -> None:
        self._items: Dict[str, Alert] = {}

    def save(self, alert: Alert) -> None:
        self._items[alert.id] = alert

    def get(self, alert_id: str) -> Optional[Alert]:
        return self._items.get(alert_id)

    def list_active(self) -> List[Alert]:
        return [
            a for a in self._items.values()
            if a.status in (AlertStatus.active, AlertStatus.acknowledged)
        ]

    def list_all(self, limit: int = 100, status: Optional[AlertStatus] = None) -> List[Alert]:
        items = list(self._items.values())
        if status is not None:
            items = [a for a in items if a.status == status]
        items.sort(key=lambda a: a.created_at, reverse=True)
        return items[:limit]

    def find_active_by_condition(self, condition: AlertCondition) -> Optional[Alert]:
        for a in self._items.values():
            if a.condition == condition and a.status in (AlertStatus.active, AlertStatus.acknowledged):
                return a
        return None

    def clear(self) -> None:
        self._items.clear()

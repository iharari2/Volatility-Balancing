from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.alert import Alert, AlertCondition, AlertStatus


class AlertRepo(ABC):
    @abstractmethod
    def save(self, alert: Alert) -> None: ...

    @abstractmethod
    def get(self, alert_id: str) -> Optional[Alert]: ...

    @abstractmethod
    def list_active(self) -> List[Alert]: ...

    @abstractmethod
    def list_all(self, limit: int = 100, status: Optional[AlertStatus] = None) -> List[Alert]: ...

    @abstractmethod
    def find_active_by_condition(self, condition: AlertCondition) -> Optional[Alert]: ...

    @abstractmethod
    def clear(self) -> None: ...

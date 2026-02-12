from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Optional

from domain.entities.alert import Alert

logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(self, webhook_url: Optional[str] = None):
        self._url = webhook_url

    @property
    def is_configured(self) -> bool:
        return bool(self._url)

    @property
    def masked_url(self) -> Optional[str]:
        if not self._url:
            return None
        if len(self._url) <= 20:
            return self._url[:8] + "..."
        return self._url[:20] + "..."

    def set_url(self, url: Optional[str]) -> None:
        self._url = url

    def send_alert(self, alert: Alert) -> bool:
        if not self._url:
            return False

        payload = {
            "text": f"[{alert.severity.value.upper()}] {alert.title}",
            "alert_id": alert.id,
            "condition": alert.condition.value,
            "severity": alert.severity.value,
            "detail": alert.detail,
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self._url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            logger.warning(f"Webhook delivery failed: {e}")
            return False

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from domain.entities.alert import Alert, AlertCondition, AlertSeverity
from application.services.webhook_service import WebhookService


@pytest.fixture
def sample_alert() -> Alert:
    return Alert.new(
        condition=AlertCondition.worker_stopped,
        severity=AlertSeverity.critical,
        title="Worker stopped",
        detail="The trading worker stopped.",
    )


def test_not_configured_returns_false(sample_alert):
    svc = WebhookService(webhook_url=None)
    assert not svc.is_configured
    assert svc.send_alert(sample_alert) is False


def test_is_configured_property():
    svc = WebhookService(webhook_url="https://hooks.slack.com/test")
    assert svc.is_configured


def test_configured_sends_post_returns_true(sample_alert):
    svc = WebhookService(webhook_url="https://hooks.slack.com/test")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        result = svc.send_alert(sample_alert)

    assert result is True
    mock_urlopen.assert_called_once()

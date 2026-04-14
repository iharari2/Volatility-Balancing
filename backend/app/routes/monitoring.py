from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.di import container
from app.auth import get_current_user, CurrentUser
from application.services.trading_worker import get_trading_worker

router = APIRouter(prefix="/v1", tags=["monitoring"])


# --- Request / Response models ---

class WebhookUpdateRequest(BaseModel):
    url: Optional[str] = None


class AlertResponse(BaseModel):
    id: str
    condition: str
    severity: str
    status: str
    title: str
    detail: str
    created_at: str
    resolved_at: Optional[str] = None
    acknowledged_at: Optional[str] = None


# --- Helpers ---

def _worker_info() -> dict:
    worker = get_trading_worker()
    return {
        "running": worker.is_running(),
        "enabled": worker.enabled,
        "interval": worker.interval_seconds,
    }


def _alert_to_dict(alert) -> Dict[str, Any]:
    return {
        "id": alert.id,
        "condition": alert.condition.value,
        "severity": alert.severity.value,
        "status": alert.status.value,
        "title": alert.title,
        "detail": alert.detail,
        "created_at": alert.created_at.isoformat(),
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "metadata": alert.metadata,
    }


# --- Endpoints ---

@router.get("/system/status")
async def system_status(user: CurrentUser = Depends(get_current_user)) -> Dict[str, Any]:
    worker = get_trading_worker()
    svc = container.system_status_service
    return svc.get_full_status(
        worker_running=worker.is_running(),
        worker_enabled=worker.enabled,
        worker_interval=worker.interval_seconds,
        last_evaluation_time=getattr(worker, "last_cycle_time", None),
    )


@router.get("/alerts")
async def list_alerts(status: Optional[str] = None, user: CurrentUser = Depends(get_current_user)) -> Dict[str, Any]:
    from domain.entities.alert import AlertStatus

    repo = container.alert_repo
    status_filter = None
    if status:
        try:
            status_filter = AlertStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    alerts = repo.list_all(limit=100, status=status_filter)
    return {
        "alerts": [_alert_to_dict(a) for a in alerts],
        "total": len(alerts),
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user: CurrentUser = Depends(get_current_user)) -> Dict[str, Any]:
    from domain.entities.alert import AlertStatus

    repo = container.alert_repo
    alert = repo.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.status == AlertStatus.resolved:
        raise HTTPException(status_code=400, detail="Alert already resolved")

    alert.status = AlertStatus.acknowledged
    alert.acknowledged_at = container.clock.now()
    repo.save(alert)
    return _alert_to_dict(alert)


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user: CurrentUser = Depends(get_current_user)) -> Dict[str, Any]:
    from domain.entities.alert import AlertStatus

    repo = container.alert_repo
    alert = repo.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = AlertStatus.resolved
    alert.resolved_at = container.clock.now()
    repo.save(alert)
    return _alert_to_dict(alert)


@router.get("/alerts/webhook")
async def get_webhook_config(user: CurrentUser = Depends(get_current_user)) -> Dict[str, Any]:
    svc = container.webhook_service
    return {
        "configured": svc.is_configured,
        "url": svc.masked_url,
    }


@router.put("/alerts/webhook")
async def set_webhook_config(req: WebhookUpdateRequest, user: CurrentUser = Depends(get_current_user)) -> Dict[str, Any]:
    svc = container.webhook_service
    svc.set_url(req.url)
    return {
        "configured": svc.is_configured,
        "url": svc.masked_url,
    }


# ── Notification preferences ──────────────────────────────────────────────────

class NotificationPrefsRequest(BaseModel):
    email_alerts: bool = True
    phone: Optional[str] = None  # stored for future SMS support


class NotificationPrefsResponse(BaseModel):
    email_alerts: bool
    phone: Optional[str]
    email_configured: bool  # whether backend SMTP is set up


@router.get("/settings/notifications")
async def get_notification_prefs(user: CurrentUser = Depends(get_current_user)) -> Dict[str, Any]:
    prefs = container._notif_prefs.get(user.user_id, {})
    return {
        "email_alerts": prefs.get("email_alerts", False),
        "phone": prefs.get("phone"),
        "email_configured": container.notification_service.is_configured,
    }


@router.put("/settings/notifications")
async def set_notification_prefs(
    req: NotificationPrefsRequest,
    user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    container._notif_prefs[user.user_id] = {
        "email_alerts": req.email_alerts,
        "phone": req.phone,
    }
    return {
        "email_alerts": req.email_alerts,
        "phone": req.phone,
        "email_configured": container.notification_service.is_configured,
    }

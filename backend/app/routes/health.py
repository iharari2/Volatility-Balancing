from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def root_health() -> Dict[str, Any]:
    try:
        from app.di import container
        from application.services.trading_worker import get_trading_worker

        worker = get_trading_worker()
        svc = container.system_status_service
        return svc.get_health(
            worker_running=worker.is_running(),
            worker_enabled=worker.enabled,
        )
    except Exception:
        return {"status": "ok"}

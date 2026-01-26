# backend/app/routes/health.py
from __future__ import annotations

from typing import Dict, Any, Optional
from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def root_health() -> Dict[str, str]:
    return {"status": "ok"}


@router.get("/workers/status")
async def workers_status() -> Dict[str, Any]:
    """Get status of all background workers."""
    from application.services.order_status_worker import OrderStatusWorkerManager

    order_status_worker = OrderStatusWorkerManager.get_instance()
    order_status_stats = order_status_worker.get_stats()

    return {
        "order_status_worker": order_status_stats or {"status": "not_initialized"},
    }


@router.get("/workers/order-status")
async def order_status_worker_detail() -> Dict[str, Any]:
    """Get detailed status of the order status worker."""
    from application.services.order_status_worker import OrderStatusWorkerManager

    manager = OrderStatusWorkerManager.get_instance()
    stats = manager.get_stats()

    if not stats:
        return {
            "status": "not_initialized",
            "message": "Order status worker has not been initialized",
        }

    return {
        "status": "running" if stats["is_running"] else "stopped",
        **stats,
    }

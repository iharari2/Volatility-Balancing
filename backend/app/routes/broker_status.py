# =========================
# backend/app/routes/broker_status.py
# =========================
"""Broker status endpoint for visibility into broker state."""

import os
import logging
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/v1/broker")
logger = logging.getLogger(__name__)


@router.get("/status")
async def broker_status() -> Dict[str, Any]:
    """
    Return current broker backend state.

    Response:
        backend: "alpaca" | "stub"
        paper: true/false (always true for stub)
        market_open: true/false
        connected: true/false
    """
    from app.di import container

    backend = os.getenv("APP_BROKER", "stub").lower()
    result: Dict[str, Any] = {
        "backend": backend,
        "paper": True,
        "market_open": False,
        "connected": False,
    }

    broker = container.broker

    # Determine paper mode
    if backend == "alpaca":
        try:
            from infrastructure.config.broker_credentials import has_alpaca_credentials
            if has_alpaca_credentials():
                paper_env = os.getenv("ALPACA_PAPER", "true").lower()
                result["paper"] = paper_env in ("true", "1", "yes", "on")
        except Exception:
            pass

    # Check market open and connectivity
    try:
        result["market_open"] = broker.is_market_open()
        result["connected"] = True
    except Exception as e:
        logger.warning("Broker connectivity check failed: %s", e)
        result["connected"] = False

    return result

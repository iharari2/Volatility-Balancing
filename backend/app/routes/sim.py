# backend/app/routes/sim.py
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body

router = APIRouter(prefix="/v1/sim", tags=["sim"])


@router.post("/tick")
def simulation_tick(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """Accept a simulation tick request and return a minimal skeleton response."""
    return {
        "status": "ok",
        "tick": {
            "events": [],
            "positions": [],
            "orders": [],
            "timeline": [],
            "received": payload,
        },
    }

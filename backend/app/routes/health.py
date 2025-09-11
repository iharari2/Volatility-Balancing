# backend/app/routes/health.py
from __future__ import annotations

from typing import Dict
from fastapi import APIRouter

router = APIRouter()


@router.get("/v1/healthz")
def root_health() -> Dict[str, str]:
    return {"status": "ok"}


# If you intentionally expose a second endpoint (as seen in openapi),
# keep this. Otherwise, you can delete it.
@router.get("/v1/v1/healthz")
def v1_health() -> Dict[str, str]:
    return {"status": "ok"}

# =========================
# backend/app/routes/health.py
# =========================
from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
def root_health():
    return {"status": "ok"}


@router.get("/v1/healthz")
def v1_health():
    return {"status": "ok", "version": "v1"}

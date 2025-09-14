# =========================
# backend/app/routes/health.py
# =========================
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def root_health():
    return {"status": "ok"}


@router.get("/v1/health")
def v1_health():
    return {"status": "ok", "version": "v1"}

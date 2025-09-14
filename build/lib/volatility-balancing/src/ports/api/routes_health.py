from fastapi import APIRouter

router = APIRouter()

@router.get("/healthz")
async def healthz():
    return {"status": "ok"}

@router.get("/v1/healthz")
async def healthz_v1():
    return {"status": "ok", "version": "v1"}
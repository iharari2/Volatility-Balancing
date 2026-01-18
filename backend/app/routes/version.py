from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/v1/version")
def version():
    # put the file somewhere stable in the repo at runtime
    # this path assumes we write it under backend/app/version.json
    p = Path(__file__).resolve().parent.parent / "version.json"  # backend/app/version.json
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {"git_sha": "unknown", "deployed_at": "unknown", "error": "bad version.json"}
    return {"git_sha": "unknown", "deployed_at": "unknown"}

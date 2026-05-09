from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import CurrentUser, get_current_user, get_auth_service
from application.services.auth_service import AuthService

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _require_owner(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    return user


class UserListItem(BaseModel):
    id: str
    tenant_id: str = ""
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: str


class UpdateUserRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None


@router.get("/users", response_model=list[UserListItem])
def list_users(
    current_user: CurrentUser = Depends(_require_owner),
    auth_service: AuthService = Depends(get_auth_service),
):
    users = auth_service.user_repo.list_all()
    return [
        UserListItem(
            id=u.id,
            tenant_id=u.tenant_id,
            email=u.email,
            display_name=u.display_name or u.email.split("@")[0],
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else "",
        )
        for u in users
    ]


class ImpersonateResponse(BaseModel):
    token: str
    user: UserListItem


@router.post("/users/{user_id}/impersonate", response_model=ImpersonateResponse)
def impersonate_user(
    user_id: str,
    current_user: CurrentUser = Depends(_require_owner),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Return a short-lived JWT scoped to the target user so an owner can preview their view."""
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot impersonate yourself")
    users = auth_service.user_repo.list_all()
    target = next((u for u in users if u.id == user_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    token = auth_service.create_access_token(target)
    return ImpersonateResponse(
        token=token,
        user=UserListItem(
            id=target.id,
            tenant_id=target.tenant_id,
            email=target.email,
            display_name=target.display_name or target.email.split("@")[0],
            role=target.role,
            is_active=target.is_active,
            created_at=target.created_at.isoformat() if target.created_at else "",
        ),
    )


@router.patch("/users/{user_id}", response_model=UserListItem)
def update_user(
    user_id: str,
    body: UpdateUserRequest,
    current_user: CurrentUser = Depends(_require_owner),
    auth_service: AuthService = Depends(get_auth_service),
):
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot modify your own account here")

    target = auth_service.user_repo.get_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    updated = auth_service.admin_update_user(
        tenant_id=target.tenant_id,
        user_id=user_id,
        role=body.role,
        is_active=body.is_active,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")

    return UserListItem(
        id=updated.id,
        email=updated.email,
        display_name=updated.display_name or updated.email.split("@")[0],
        role=updated.role,
        is_active=updated.is_active,
        created_at=updated.created_at.isoformat() if updated.created_at else "",
    )


# ── Blackout detection & backfill ────────────────────────────────────────────

@router.get("/blackouts/report")
def blackout_report(
    current_user: CurrentUser = Depends(_require_owner),
) -> List[Dict[str, Any]]:
    """Return blackout periods found across all live positions (read-only, no backfill)."""
    from app.di import container

    results = []
    try:
        positions = container.positions.list_all()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not list positions: {exc}")

    uc = container.backfill_blackout_uc
    for position in positions:
        if getattr(position, "asset_symbol", None) in (None, "CASH"):
            continue
        try:
            blackouts = uc._find_blackouts(position.id, position.asset_symbol)
            results.append(
                {
                    "position_id": position.id,
                    "ticker": position.asset_symbol,
                    "blackouts": [
                        {
                            "start": b.start.isoformat(),
                            "end": b.end.isoformat(),
                            "calendar_days": b.calendar_days,
                            "duration_hours": round(b.duration_hours, 1),
                        }
                        for b in blackouts
                    ],
                }
            )
        except Exception as exc:
            results.append(
                {"position_id": position.id, "ticker": position.asset_symbol, "error": str(exc)}
            )
    return results


@router.post("/blackouts/backfill")
def trigger_backfill(
    position_id: str | None = None,
    current_user: CurrentUser = Depends(_require_owner),
) -> List[Dict[str, Any]]:
    """
    Trigger blackout backfill immediately.

    Pass ?position_id=<id> to backfill a single position, or omit to backfill all.
    Applies missed dividends to position cash and replays evaluations in the timeline.
    """
    from app.di import container

    uc = container.backfill_blackout_uc
    try:
        if position_id:
            position = container.positions.get(position_id)
            if not position:
                raise HTTPException(status_code=404, detail="Position not found")
            results = [uc.backfill_position(position)]
        else:
            results = uc.backfill_all_positions()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Backfill failed: {exc}")

    return [r.to_dict() for r in results]

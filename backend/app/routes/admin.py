from __future__ import annotations

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
    users = auth_service.list_users(current_user.tenant_id)
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
    users = auth_service.list_users(current_user.tenant_id)
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

    updated = auth_service.admin_update_user(
        tenant_id=current_user.tenant_id,
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

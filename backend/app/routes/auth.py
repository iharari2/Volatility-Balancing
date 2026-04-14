from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import CurrentUser, get_current_user, get_auth_service
from app.di import container
from application.services.auth_service import AuthService

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class UserResponse(BaseModel):
    id: str
    tenant_id: str
    email: str
    display_name: str
    role: str


@router.post("/register", response_model=AuthResponse)
def register(
    body: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        user, token = auth_service.register(body.email, body.password, body.display_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Auto-create a default portfolio for the new user
    try:
        import uuid
        from domain.entities.portfolio import Portfolio
        portfolio = Portfolio(
            id=str(uuid.uuid4()),
            tenant_id=user.tenant_id,
            name=f"{user.display_name or user.email.split('@')[0]}'s Portfolio",
            description="Default portfolio",
            user_id=user.id,
            trading_state="RUNNING",
        )
        container.portfolio_repo.create(portfolio)
    except Exception:
        pass  # Don't fail registration if portfolio creation fails

    return AuthResponse(
        token=token,
        user=UserResponse(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
        ),
    )


@router.post("/login", response_model=AuthResponse)
def login(
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        user, token = auth_service.login(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return AuthResponse(
        token=token,
        user=UserResponse(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
        ),
    )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    user: CurrentUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        auth_service.change_password(user.user_id, body.current_password, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Password changed successfully"}


class ForgotPasswordRequest(BaseModel):
    email: str


@router.post("/forgot-password")
def forgot_password(
    body: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Initiate password reset. Always returns 200 to avoid leaking user existence.
    If the email is registered, sends a reset link via email.
    """
    user = auth_service.user_repo.get_by_email_global(body.email)
    if user:
        token = container.password_reset_service.create_token(user.id, user.email)
        base_url = os.getenv("APP_BASE_URL", "http://localhost:5173")
        reset_url = f"{base_url}/reset-password?token={token}"
        container.notification_service.send_password_reset_email(user.email, reset_url)
    return {"message": "If that email is registered, a reset link has been sent."}


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password")
def reset_password(
    body: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = container.password_reset_service.consume_token(body.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = auth_service.user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from application.services.auth_service import _hash_password
    from datetime import datetime, timezone
    user.hashed_password = _hash_password(body.new_password)
    user.updated_at = datetime.now(timezone.utc)
    auth_service.user_repo.update(user)
    return {"message": "Password reset successfully"}


class UpdateProfileRequest(BaseModel):
    display_name: str


@router.get("/me", response_model=UserResponse)
def me(
    user: CurrentUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    db_user = auth_service.user_repo.get_by_id(user.user_id)
    return UserResponse(
        id=user.user_id,
        tenant_id=user.tenant_id,
        email=user.email,
        display_name=(db_user.display_name if db_user and db_user.display_name else user.email.split("@")[0]),
        role=user.role,
    )


@router.put("/me", response_model=UserResponse)
def update_me(
    body: UpdateProfileRequest,
    user: CurrentUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    from datetime import datetime, timezone
    db_user = auth_service.user_repo.get_by_id(user.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.display_name = body.display_name.strip()
    db_user.updated_at = datetime.now(timezone.utc)
    auth_service.user_repo.update(db_user)
    return UserResponse(
        id=user.user_id,
        tenant_id=user.tenant_id,
        email=user.email,
        display_name=db_user.display_name,
        role=user.role,
    )

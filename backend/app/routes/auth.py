from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from app.auth import CurrentUser, get_current_user, get_auth_service
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


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser = Depends(get_current_user)):
    return UserResponse(
        id=user.user_id,
        tenant_id=user.tenant_id,
        email=user.email,
        display_name=user.email.split("@")[0],
        role=user.role,
    )

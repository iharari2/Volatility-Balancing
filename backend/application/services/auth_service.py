from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import bcrypt
from jose import JWTError, jwt

from domain.entities.user import User
from domain.ports.user_repo import UserRepo


def _hash_password(password: str) -> str:
    """Hash password using bcrypt directly."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def _verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))


class AuthService:
    def __init__(
        self,
        user_repo: UserRepo,
        secret_key: str,
        algorithm: str = "HS256",
        token_expire_hours: int = 24,
    ):
        self.user_repo = user_repo
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_hours = token_expire_hours

    def register(
        self, email: str, password: str, display_name: str = ""
    ) -> Tuple[User, str]:
        # Check if email already exists globally
        existing = self.user_repo.get_by_email_global(email)
        if existing:
            raise ValueError("Email already registered")

        # First user globally gets tenant_id="default" and owner role (the platform admin)
        # All subsequent users get their own tenant and member role
        total_default = self.user_repo.count_by_tenant("default")
        is_first_user = total_default == 0
        if is_first_user:
            tenant_id = "default"
            role = "owner"
        else:
            tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
            role = "member"

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=email,
            hashed_password=_hash_password(password),
            display_name=display_name or email.split("@")[0],
            role=role,
        )
        self.user_repo.create(user)
        token = self.create_access_token(user)
        return user, token

    def login(self, email: str, password: str) -> Tuple[User, str]:
        user = self.user_repo.get_by_email_global(email)
        if not user or not _verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is disabled")
        token = self.create_access_token(user)
        return user, token

    def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if not _verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters")
        user.hashed_password = _hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        self.user_repo.update(user)

    def create_access_token(self, user: User) -> str:
        expire = datetime.now(timezone.utc) + timedelta(hours=self.token_expire_hours)
        payload = {
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "email": user.email,
            "role": user.role,
            "exp": expire,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError:
            return None

    def list_users(self, tenant_id: str) -> list[User]:
        return self.user_repo.list_by_tenant(tenant_id)

    def admin_update_user(
        self,
        tenant_id: str,
        user_id: str,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[User]:
        user = self.user_repo.get_by_id(user_id)
        if not user or user.tenant_id != tenant_id:
            return None
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        user.updated_at = datetime.now(timezone.utc)
        return self.user_repo.update(user)

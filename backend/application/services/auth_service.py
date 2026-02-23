from __future__ import annotations

import hashlib
import base64
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext

from domain.entities.user import User
from domain.ports.user_repo import UserRepo


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _prehash(password: str) -> str:
    """Pre-hash password with SHA-256 to avoid bcrypt's 72-byte limit."""
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest()).decode("ascii")


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

        # First user globally gets tenant_id="default" to preserve existing data
        total_default = self.user_repo.count_by_tenant("default")
        if total_default == 0:
            tenant_id = "default"
        else:
            tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=email,
            hashed_password=pwd_context.hash(_prehash(password)),
            display_name=display_name or email.split("@")[0],
            role="owner",
        )
        self.user_repo.create(user)
        token = self.create_access_token(user)
        return user, token

    def login(self, email: str, password: str) -> Tuple[User, str]:
        user = self.user_repo.get_by_email_global(email)
        if not user or not pwd_context.verify(_prehash(password), user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is disabled")
        token = self.create_access_token(user)
        return user, token

    def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if not pwd_context.verify(_prehash(current_password), user.hashed_password):
            raise ValueError("Current password is incorrect")
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters")
        user.hashed_password = pwd_context.hash(_prehash(new_password))
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

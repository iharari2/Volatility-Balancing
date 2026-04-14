from __future__ import annotations

from typing import Optional

from domain.entities.user import User


class InMemoryUserRepo:
    def __init__(self):
        self._users: dict[str, User] = {}

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def get_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        for u in self._users.values():
            if u.tenant_id == tenant_id and u.email == email:
                return u
        return None

    def get_by_email_global(self, email: str) -> Optional[User]:
        for u in self._users.values():
            if u.email == email:
                return u
        return None

    def create(self, user: User) -> User:
        self._users[user.id] = user
        return user

    def update(self, user: User) -> User:
        self._users[user.id] = user
        return user

    def count_by_tenant(self, tenant_id: str) -> int:
        return sum(1 for u in self._users.values() if u.tenant_id == tenant_id)

    def list_by_tenant(self, tenant_id: str) -> list[User]:
        return [u for u in self._users.values() if u.tenant_id == tenant_id]

    def list_all(self) -> list[User]:
        return list(self._users.values())

    def clear(self) -> None:
        self._users.clear()

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import sessionmaker

from domain.entities.user import User
from infrastructure.persistence.sql.models import UserModel


class SQLUserRepo:
    def __init__(self, session_factory: sessionmaker):
        self._sf = session_factory

    def _to_entity(self, m: UserModel) -> User:
        return User(
            id=m.id,
            tenant_id=m.tenant_id,
            email=m.email,
            hashed_password=m.hashed_password,
            display_name=m.display_name,
            role=m.role,
            is_active=m.is_active,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def get_by_id(self, user_id: str) -> Optional[User]:
        with self._sf() as s:
            m = s.query(UserModel).filter(UserModel.id == user_id).first()
            return self._to_entity(m) if m else None

    def get_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        with self._sf() as s:
            m = (
                s.query(UserModel)
                .filter(UserModel.tenant_id == tenant_id, UserModel.email == email)
                .first()
            )
            return self._to_entity(m) if m else None

    def get_by_email_global(self, email: str) -> Optional[User]:
        with self._sf() as s:
            m = s.query(UserModel).filter(UserModel.email == email).first()
            return self._to_entity(m) if m else None

    def create(self, user: User) -> User:
        with self._sf() as s:
            m = UserModel(
                id=user.id,
                tenant_id=user.tenant_id,
                email=user.email,
                hashed_password=user.hashed_password,
                display_name=user.display_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            s.add(m)
            s.commit()
            return user

    def update(self, user: User) -> User:
        with self._sf() as s:
            m = s.query(UserModel).filter(UserModel.id == user.id).first()
            if m:
                m.hashed_password = user.hashed_password
                m.display_name = user.display_name
                m.role = user.role
                m.is_active = user.is_active
                m.updated_at = user.updated_at
                s.commit()
            return user

    def count_by_tenant(self, tenant_id: str) -> int:
        with self._sf() as s:
            return s.query(UserModel).filter(UserModel.tenant_id == tenant_id).count()

    def clear(self) -> None:
        with self._sf() as s:
            s.query(UserModel).delete()
            s.commit()

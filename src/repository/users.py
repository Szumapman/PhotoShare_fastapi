from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.repository.abstract import AbstractUserRepo
from src.schemas.users import UserIn, ActiveStatus, UserRoleIn
from src.database.models import User, RefreshToken, LogoutAccessToken
from src.conf.constant import (
    TOKEN_NOT_FOUND,
    ACCESS_TOKEN_EXPIRE,
    TOKEN_DELETED,
    USER_NOT_FOUND,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    FORBIDDEN_OPERATION_ON_ADMIN_ACCOUNT,
)


class PostgresUserRepo(AbstractUserRepo):
    def __init__(self, db: Session):
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    async def get_user_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    async def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    async def get_users(self) -> list[User]:
        return self.db.query(User).all()

    async def create_user(self, user: UserIn, avatar: str) -> User:
        new_user = User(
            username=user.username,
            email=user.email,
            password=user.password,
            avatar=avatar,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    async def update_user(self, new_user_data: UserIn, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        user.username = new_user_data.username
        user.email = new_user_data.email
        user.password = new_user_data.password
        self.db.commit()
        self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> User | str:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            return USER_NOT_FOUND
        self.db.delete(user)
        self.db.commit()
        return user

    async def add_refresh_token(
        self, user: User, token: str | None, expiration_date: datetime, session_id: str
    ) -> None:
        refresh_token = RefreshToken(
            refresh_token=token,
            user_id=user.id,
            session_id=session_id,
            expires_at=expiration_date,
        )
        self.db.add(refresh_token)
        self.db.commit()

    async def delete_refresh_token(self, token: str, user_id: int) -> str:
        old_token = (
            self.db.query(RefreshToken)
            .filter(
                and_(
                    RefreshToken.refresh_token == token, RefreshToken.user_id == user_id
                )
            )
            .first()
        )
        if old_token is None:
            return TOKEN_NOT_FOUND
        self.db.delete(old_token)
        self.db.commit()
        return TOKEN_DELETED

    async def logout_user(self, token: str, session_id: str, user: User) -> User | str:
        refresh_token = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.session_id == session_id, RefreshToken.user_id == user.id
            )
            .first()
        )
        if refresh_token is None:
            return TOKEN_NOT_FOUND
        self.db.delete(refresh_token)
        logout_access_token = LogoutAccessToken(
            logout_access_token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE),
        )
        self.db.add(logout_access_token)
        self.db.commit()
        return user

    async def is_user_logout(self, token: str) -> bool:
        return (
            self.db.query(LogoutAccessToken)
            .filter(LogoutAccessToken.logout_access_token == token)
            .first()
        )

    async def set_user_active_status(
        self, user_id: int, active_status: ActiveStatus, current_user: User
    ) -> User | str:
        user = await self.get_user_by_id(user_id)
        if user is None:
            return USER_NOT_FOUND
        if user.role == ROLE_ADMIN and current_user.role == ROLE_MODERATOR:
            return FORBIDDEN_OPERATION_ON_ADMIN_ACCOUNT
        user.is_active = active_status.is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    async def set_user_role(self, user_id: int, role: UserRoleIn) -> User | str:
        user = await self.get_user_by_id(user_id)
        if user is None:
            return USER_NOT_FOUND
        user.role = role.role
        self.db.commit()
        self.db.refresh(user)
        return user

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.repository.abstract import AbstractUserRepo
from src.schemas.users import UserIn
from src.database.models import User, RefreshToken, LogoutAccessToken
from src.services.avatar import AvatarProviderGravatar
from src.conf.constant import TOKEN_NOT_FOUND, ACCESS_TOKEN_EXPIRE, TOKEN_DELETED


class PostgresUserRepo(AbstractUserRepo):
    def __init__(self, db: Session):
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(email=email).first()

    async def get_user_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(username=username).first()

    async def create_user(self, user: UserIn) -> User:
        avatar = AvatarProviderGravatar(user.email).get_avatar(255)
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
            .filter(refresh_token=token, user_id=user_id)
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
            .filter(session_id=session_id, user_id=user.id)
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
            self.db.query(LogoutAccessToken).filter(logout_access_token=token).first()
            is not None
        )

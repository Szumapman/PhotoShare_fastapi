from datetime import datetime

from sqlalchemy.orm import Session

from src.repository.abstract import AbstractUser
from src.schemas.users import UserIn
from src.database.models import User, RefreshToken
from src.services.avatar import AvatarProviderGravatar
from src.conf.constant import TOKEN_NOT_FOUND


class PostgresUser(AbstractUser):
    def __init__(self, db: Session):
        self.db = db

    async def get_user_by_email(self, email: str) -> User:
        return self.db.query(User).filter(User.email == email).first()

    async def get_user_by_username(self, username: str) -> User:
        return self.db.query(User).filter(User.username == username).first()

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

    async def delete_refresh_token(
        self, token: str, user_id: int
    ) -> RefreshToken | str:
        old_token = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.refresh_token == token, RefreshToken.user_id == user_id
            )
            .first()
        )
        if old_token is None:
            return TOKEN_NOT_FOUND
        self.db.delete(old_token)
        self.db.commit()
        return old_token

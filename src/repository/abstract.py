import abc
from datetime import datetime

from src.schemas.users import UserDb, UserIn
from src.database.models import User


class AbstractUser(abc.ABC):
    @abc.abstractmethod
    async def get_user_by_email(self, email: str) -> User:
        pass

    @abc.abstractmethod
    async def get_user_by_username(self, username: str) -> User:
        pass

    @abc.abstractmethod
    async def create_user(self, user: UserIn) -> User:
        pass

    @abc.abstractmethod
    async def add_refresh_token(
        self, user: User, token: str | None, expiration_date: datetime, session_id: str
    ) -> None:
        pass

    @abc.abstractmethod
    async def delete_refresh_token(self, token: str, user_id: int):
        pass

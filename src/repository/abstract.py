import abc

from src.schemas.users import UserDb, UserIn
from src.database.models import User


class AbstractUser(abc.ABC):
    @abc.abstractmethod
    async def get_user_by_email(self, email: str) -> User:
        pass

    @abc.abstractmethod
    async def create_user(self, user: UserIn) -> User:
        pass

    @abc.abstractmethod
    async def update_token(self, user: User, token: str | None) -> None:
        pass

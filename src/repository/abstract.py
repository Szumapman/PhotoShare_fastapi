import abc
from datetime import datetime

from src.schemas.users import UserIn, ActiveStatus, UserRoleIn
from src.database.models import User


class AbstractUserRepo(abc.ABC):
    @abc.abstractmethod
    async def get_user_by_email(self, email: str) -> User:
        pass

    @abc.abstractmethod
    async def get_user_by_username(self, username: str) -> User:
        pass

    @abc.abstractmethod
    async def get_user_by_id(self, user_id: int) -> User:
        pass

    @abc.abstractmethod
    async def get_users(self) -> list[User]:
        pass

    @abc.abstractmethod
    async def create_user(self, user: UserIn, avatar: str) -> User:
        pass

    @abc.abstractmethod
    async def update_user(self, new_user_data: UserIn, user_id: int) -> User:
        pass

    @abc.abstractmethod
    async def delete_user(self, user_id: int) -> User:
        pass

    @abc.abstractmethod
    async def add_refresh_token(
        self, user: User, token: str | None, expiration_date: datetime, session_id: str
    ) -> None:
        pass

    @abc.abstractmethod
    async def delete_refresh_token(self, token: str, user_id: int):
        pass

    @abc.abstractmethod
    async def logout_user(self, token: str, session_id: str, user: User) -> User | str:
        pass

    @abc.abstractmethod
    async def is_user_logout(self, token: str) -> bool:
        pass

    @abc.abstractmethod
    async def set_user_active_status(
        self, user_id: int, active_status: ActiveStatus, current_user: User
    ) -> User | str:
        pass

    @abc.abstractmethod
    async def set_user_role(self, user_id: int, role: UserRoleIn) -> User | str:
        pass

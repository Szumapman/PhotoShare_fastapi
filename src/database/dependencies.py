from src.database.db import get_db
from src.repository.abstract import AbstractUserRepo
from src.repository.users import PostgresUserRepo
from src.services.abstract import AbstractAvatarProvider
from src.services.avatar import AvatarProviderGravatar
from src.services.abstract import AbstractPasswordHandler
from src.services.password import BcryptPasswordHandler


def get_password_handler() -> AbstractPasswordHandler:
    return BcryptPasswordHandler()


def get_avatar_provider() -> AbstractAvatarProvider:
    return AvatarProviderGravatar()


def get_user_repository() -> AbstractUserRepo:
    return PostgresUserRepo(next(get_db()))

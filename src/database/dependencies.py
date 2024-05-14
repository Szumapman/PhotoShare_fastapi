from src.database.db import get_db
from src.repository.abstract import AbstractUser
from src.repository.users import PostgresUser


def get_user_repository() -> AbstractUser:
    return PostgresUser(next(get_db()))

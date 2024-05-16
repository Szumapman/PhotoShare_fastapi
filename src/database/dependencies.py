from src.database.db import get_db
from src.repository.abstract import AbstractUserRepo
from src.repository.users import PostgresUserRepo


def get_user_repository() -> AbstractUserRepo:
    return PostgresUserRepo(next(get_db()))

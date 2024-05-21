from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from src.database.models import Base, User
from src.database.dependencies import get_user_repository, get_avatar_provider
from src.repository.users import PostgresUserRepo
from src.services.avatar import AvatarProviderGravatar
from src.conf.constant import ROLE_ADMIN, ROLE_MODERATOR, ROLE_STANDARD, API, AUTH

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

USERNAME_STANDARD = "test user"
EMAIL_STANDARD = "test@email.com"
PASSWORD_STANDARD = "Password1!"


@pytest.fixture(scope="module")
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def client(session):

    def override_get_user_repository():
        try:
            yield PostgresUserRepo(session)
        finally:
            session.close()

    def override_get_avatar_provider():
        try:
            yield AvatarProviderGravatar()
        finally:
            session.close()

    app.dependency_overrides = {
        get_user_repository: override_get_user_repository,
        get_avatar_provider: override_get_avatar_provider,
    }

    yield TestClient(app)


@pytest.fixture(scope="function")
def user_in_standard_json():
    return {
        "username": USERNAME_STANDARD,
        "email": EMAIL_STANDARD,
        "password": PASSWORD_STANDARD,
    }


@pytest.fixture(scope="function")
def user_db_standard():
    return User(
        id=2,
        username=USERNAME_STANDARD,
        email=EMAIL_STANDARD,
        password="<HASHED-PASSWORD>",
        role=ROLE_STANDARD,
        created_at=datetime.utcnow(),
        avatar="avatar_url",
        is_active=True,
    )


@pytest.fixture(scope="module")
def tokens(session, client):
    user = session.query(User).filter(User.email == EMAIL_STANDARD).first()
    user.is_active = True
    session.commit()
    response = client.post(
        f"{API}{AUTH}/login",
        data={
            "username": EMAIL_STANDARD,
            "password": PASSWORD_STANDARD,
        },
    )
    data = response.json()
    return data

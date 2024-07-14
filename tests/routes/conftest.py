from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from fastapi import File
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from src.database.models import Base, User, Photo
from src.database.dependencies import (
    get_user_repository,
    get_avatar_provider,
    get_photo_repository,
    get_photo_storage_provider,
    get_qr_code_provider,
)
from src.repository.users import PostgresUserRepo
from src.repository.photos import PostgresPhotoRepo
from src.schemas.photos import PhotoOut, TransformIn
from src.services.abstract import AbstractPhotoStorageProvider, AbstractQrCodeProvider
from src.services.avatar import AvatarProviderGravatar
from src.conf.constant import ROLE_ADMIN, ROLE_MODERATOR, ROLE_STANDARD, API, AUTH


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

USERNAME_STANDARD = "test user"
USERNAME_ADMIN = "test admin"
USERNAME_MODERATOR = "test moderator"
EMAIL_STANDARD = "test@email.com"
EMAIL_ADMIN = "test_admin@email.com"
EMAIL_MODERATOR = "test_moderator@email.com"
PASSWORD = "Password1!"

PHOTO_URL = "test_photo_url"
AVATAR_URL = "test_avatar_url"
TRANSFORM_PHOTO_URL = "test_transform_photo_url"
TRANSFORM_PARAMS = ["param1", "param2"]


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
def client_app(session):

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

    def override_get_photo_repository():
        try:
            yield PostgresPhotoRepo(session)
        finally:
            session.close()

    def override_get_photo_storage_provider():
        return MockCloudinaryPhotoStorageProvider()

    app.dependency_overrides = {
        get_user_repository: override_get_user_repository,
        get_avatar_provider: override_get_avatar_provider,
        get_photo_repository: override_get_photo_repository,
        get_photo_storage_provider: override_get_photo_storage_provider,
    }

    yield TestClient(app)


@pytest.fixture(scope="function")
def user_in_standard_json():
    return {
        "username": USERNAME_STANDARD,
        "email": EMAIL_STANDARD,
        "password": PASSWORD,
    }


@pytest.fixture(scope="function")
def user_in_admin_json():
    return {
        "username": USERNAME_ADMIN,
        "email": EMAIL_ADMIN,
        "password": PASSWORD,
    }


@pytest.fixture(scope="function")
def user_in_moderator_json():
    return {
        "username": USERNAME_MODERATOR,
        "email": EMAIL_MODERATOR,
        "password": PASSWORD,
    }


@pytest.fixture(scope="module")
def tokens(session, client_app):
    user = session.query(User).filter(User.email == EMAIL_STANDARD).first()
    user.is_active = True
    session.commit()
    response = client_app.post(
        f"{API}{AUTH}/login",
        data={
            "username": EMAIL_STANDARD,
            "password": PASSWORD,
        },
    )
    data = response.json()
    return data


@pytest.fixture(scope="function")
def access_token_user_standard(session, client_app, user_in_standard_json):
    client_app.post(f"{API}{AUTH}/signup", json=user_in_standard_json)
    response = client_app.post(
        f"{API}{AUTH}/login",
        data={
            "username": EMAIL_STANDARD,
            "password": PASSWORD,
        },
    )
    data = response.json()
    return data["access_token"]


@pytest.fixture(scope="function")
def access_token_user_admin(session, client_app, user_in_admin_json):
    client_app.post(f"{API}{AUTH}/signup", json=user_in_admin_json)
    response = client_app.post(
        f"{API}{AUTH}/login",
        data={
            "username": EMAIL_ADMIN,
            "password": PASSWORD,
        },
    )
    data = response.json()
    session.query(User).filter(User.email == EMAIL_ADMIN).update(
        {
            "role": ROLE_ADMIN,
            "is_active": True,
        }
    )
    return data["access_token"]


@pytest.fixture(scope="function")
def access_token_user_moderator(session, client_app, user_in_moderator_json):
    client_app.post(f"{API}{AUTH}/signup", json=user_in_moderator_json)
    response = client_app.post(
        f"{API}{AUTH}/login",
        data={
            "username": EMAIL_MODERATOR,
            "password": PASSWORD,
        },
    )
    data = response.json()
    session.query(User).filter(User.email == EMAIL_MODERATOR).update(
        {
            "role": ROLE_MODERATOR,
            "is_active": True,
        }
    )
    return data["access_token"]


@pytest.fixture(scope="module")
def photo_in_json():
    return {
        "description": "test description",
        "tags": [{"name": "tag1 test"}, {"name": "tag2 test"}],
    }


@pytest.fixture(scope="function")
def photo():
    return Photo(
        id=1,
        description="test description",
        photo_url=PHOTO_URL,
        user_id=1,
    )


@pytest.fixture(scope="function")
def photo_2():
    return Photo(
        id=2,
        description="another text",
        photo_url=PHOTO_URL,
        user_id=2,
    )


class MockCloudinaryPhotoStorageProvider(AbstractPhotoStorageProvider):
    async def upload_photo(self, photo: File) -> str:
        return PHOTO_URL

    async def upload_avatar(self, avatar: File) -> str:
        return AVATAR_URL

    async def delete_photo(self, photo_url: str) -> None:
        pass

    async def transform_photo(
        self, photo_url: str, transform: TransformIn
    ) -> (str, list[str]):
        return TRANSFORM_PHOTO_URL, TRANSFORM_PARAMS

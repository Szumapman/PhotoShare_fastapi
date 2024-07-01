from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import status

from src.services.auth import auth_service
from src.database.models import User, RefreshToken, Photo
from src.schemas.users import UserInfo, UserDb, UserIn
from src.conf.constant import (
    USER_CREATED,
    AUTH,
    API,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_STANDARD,
    INCORRECT_USERNAME_OR_PASSWORD,
    BANNED_USER,
    COULD_NOT_VALIDATE_CREDENTIALS,
    INVALID_SCOPE,
    TOKEN_NOT_FOUND,
    PHOTO_NOT_FOUND,
    FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR,
)
from tests.routes.conftest import (
    EMAIL_STANDARD,
    PHOTO_URL,
    QR_CODE_URL,
    EMAIL_ADMIN,
    EMAIL_MODERATOR,
)
from src.conf.constant import PHOTOS
from src.schemas.photos import PhotoIn


def test_create_photo_success(client_app, photo_in_json, access_token_user_standard):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        photo_in_data = PhotoIn(**photo_in_json)
        with open("tests/static/test.jpg", "rb") as file:
            response = client_app.post(
                f"{API}{PHOTOS}/",
                data={"photo_info": photo_in_data.model_dump_json()},
                files={"photo": file},
                headers={"Authorization": f"Bearer {access_token_user_standard}"},
            )
        assert response.status_code == status.HTTP_201_CREATED, response.text
        data = response.json()
        assert data["photo_url"] == PHOTO_URL
        assert data["qr_url"] == QR_CODE_URL
        assert "id" in data


def test_get_photo_success(session, client_app, photo, access_token_user_standard):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}/{photo.id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["id"] == photo.id
    assert data["photo_url"] == PHOTO_URL
    assert data["qr_url"] == QR_CODE_URL


def test_get_photo_fail(session, client_app, access_token_user_standard):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}/-1",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        assert response.json()["detail"] == PHOTO_NOT_FOUND


def test_delete_photo_success(session, client_app, photo, access_token_user_standard):
    user = session.query(User).filter(User.email == EMAIL_STANDARD).first()
    session.query(Photo).delete()
    session.commit()
    photo.user_id = user.id
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{PHOTOS}/{photo.id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["id"] == photo.id


def test_delete_photo_by_admin_success(
    session, client_app, photo, access_token_user_admin
):
    user = session.query(User).filter(User.email == EMAIL_ADMIN).first()
    user.role = ROLE_ADMIN
    session.add(user)
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{PHOTOS}/{photo.id}",
            headers={"Authorization": f"Bearer {access_token_user_admin}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["id"] == photo.id


def test_delete_fail_wrong_user_id(
    session, client_app, photo, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    photo.user_id = 999
    session.add(photo)
    session.commit()
    session.refresh(photo)
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{PHOTOS}/{photo.id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
        assert response.json()["detail"] == FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR


def test_delete_by_moderator_fail(
    session, client_app, photo, access_token_user_moderator
):
    session.query(Photo).delete()
    session.commit()
    user = session.query(User).filter(User.email == EMAIL_MODERATOR).first()
    user.role = ROLE_MODERATOR
    session.add(user)
    photo.user_id = 999
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{PHOTOS}/{photo.id}",
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
    assert response.json()["detail"] == FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR

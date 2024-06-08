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
)
from tests.routes.conftest import EMAIL_STANDARD, PHOTO_URL, QR_CODE_URL
from src.conf.constant import PHOTOS
from src.schemas.photos import PhotoIn


def test_create_photo_success(client_app, photo_in_json, access_token):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        photo_in_data = PhotoIn(**photo_in_json)
        with open("tests/static/test.jpg", "rb") as file:
            response = client_app.post(
                f"{API}{PHOTOS}/",
                data={"photo_info": photo_in_data.model_dump_json()},
                files={"photo": file},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        assert response.status_code == status.HTTP_201_CREATED, response.text
        data = response.json()
        assert data["photo_url"] == PHOTO_URL
        assert data["qr_url"] == QR_CODE_URL
        assert "id" in data


def test_get_photo_success(session, client_app, photo, access_token):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}/{photo.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["id"] == photo.id
    assert data["photo_url"] == PHOTO_URL
    assert data["qr_url"] == QR_CODE_URL


def test_get_photo_fail(session, client_app, access_token):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}/-1",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        assert response.json()["detail"] == PHOTO_NOT_FOUND

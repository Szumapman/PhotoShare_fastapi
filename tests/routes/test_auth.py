from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import status

from src.services.auth import auth_service
from src.database.models import User, RefreshToken
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
)
from tests.routes.conftest import (
    EMAIL_STANDARD,
    USERNAME_STANDARD,
    PHOTO_URL,
    QR_CODE_URL,
)
from src.repository.users import PostgresUserRepo


def test_signup_success(client_app, user_in_standard_json):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(f"{API}{AUTH}/signup", json=user_in_standard_json)
        assert response.status_code == status.HTTP_201_CREATED, response.text
        data = response.json()
        assert data["detail"] == USER_CREATED
        assert data["user"]["username"] == USERNAME_STANDARD
        assert data["user"]["email"] == EMAIL_STANDARD
        assert data["user"]["role"] == ROLE_STANDARD


def test_signup_fail(client_app, user_in_standard_json):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(f"{API}{AUTH}/signup", json=user_in_standard_json)
        assert response.status_code == status.HTTP_409_CONFLICT, response.text
        data = response.json()
        assert data["detail"] == "Account with this email already exists"
        user_in_standard_json["email"] = "another@email.com"
        response = client_app.post(f"{API}{AUTH}/signup", json=user_in_standard_json)
        assert response.status_code == status.HTTP_409_CONFLICT, response.text
        data = response.json()
        assert data["detail"] == "Account with this username already exists"


def test_login_success(client_app, user_in_standard_json):
    response = client_app.post(
        f"{API}{AUTH}/login",
        data={
            "username": user_in_standard_json.get("email"),
            "password": user_in_standard_json.get("password"),
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


def test_login_fail_wrong_email(client_app, user_in_standard_json):
    response = client_app.post(
        f"{API}{AUTH}/login",
        data={
            "username": "wrong_email@email.com",
            "password": user_in_standard_json.get("password"),
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    data = response.json()
    assert data["detail"] == INCORRECT_USERNAME_OR_PASSWORD


def test_login_fail_wrong_password(client_app, user_in_standard_json):
    response = client_app.post(
        f"{API}{AUTH}/login",
        data={
            "username": user_in_standard_json.get("email"),
            "password": "wrong_password",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    data = response.json()
    assert data["detail"] == INCORRECT_USERNAME_OR_PASSWORD


def test_login_fail_user_banned(session, client_app, user_in_standard_json):
    user = (
        session.query(User).filter_by(email=user_in_standard_json.get("email")).first()
    )
    user.is_active = False
    session.commit()
    response = client_app.post(
        f"{API}{AUTH}/login",
        data={
            "username": user_in_standard_json.get("email"),
            "password": user_in_standard_json.get("password"),
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
    data = response.json()
    assert data["detail"] == BANNED_USER


def test_refresh_token_success(client_app, tokens):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{AUTH}/refresh_token",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["token_type"] == "bearer"


def test_refresh_token_wrong_token(client_app, tokens):
    wrong_refresh_token = tokens["refresh_token"] + "_wrong"
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{AUTH}/refresh_token",
            headers={"Authorization": f"Bearer {wrong_refresh_token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
        data = response.json()
        assert data["detail"] == COULD_NOT_VALIDATE_CREDENTIALS

        response = client_app.get(
            f"{API}{AUTH}/refresh_token",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
        data = response.json()
        assert data["detail"] == INVALID_SCOPE


def test_refresh_token_no_user(
    session,
    client_app,
    tokens,
):
    user = session.query(User).filter(User.email == EMAIL_STANDARD).first()
    session.delete(user)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{AUTH}/refresh_token",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        assert data["detail"] == "User not found"

from unittest.mock import patch

from fastapi import status

from src.conf.constant import (
    USER_CREATED,
    API,
    USERS,
    ROLE_STANDARD,
    INCORRECT_USERNAME_OR_PASSWORD,
    BANNED_USER,
    COULD_NOT_VALIDATE_CREDENTIALS,
    INVALID_SCOPE,
    USER_LOGOUT,
    LOG_IN_AGAIN,
    USER_NOT_FOUND,
    USERNAME_EXISTS,
    EMAIL_EXISTS,
)
from src.database.models import User
from src.schemas.users import UserDb
from src.services.auth import auth_service
from tests.routes.conftest import (
    EMAIL_STANDARD,
    EMAIL_MODERATOR,
    USERNAME_MODERATOR,
    USERNAME_STANDARD,
)


def test_get_users_success(
    client_app,
    access_token_user_admin,
    access_token_user_moderator,
    access_token_user_standard,
):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{USERS}",
            headers={"Authorization": f"Bearer {access_token_user_admin}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert len(data) == 3
        assert "role" in data[0]

        response = client_app.get(
            f"{API}{USERS}",
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert len(data) == 3
        assert "is_active" in data[0]

        response = client_app.get(
            f"{API}{USERS}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert len(data) == 3
        assert "is_active" not in data[0]
        assert "role" not in data[0]
        assert "id" in data[0]


def test_get_user_success(
    session,
    client_app,
    access_token_user_admin,
    access_token_user_moderator,
    access_token_user_standard,
):
    user_moderator = session.query(User).filter_by(email=EMAIL_MODERATOR).first()
    user_standard = session.query(User).filter_by(email=EMAIL_STANDARD).first()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{USERS}/{user_moderator.id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["id"] == user_moderator.id
        assert "is_active" not in data
        assert "role" not in data

        response = client_app.get(
            f"{API}{USERS}/{user_standard.id}",
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["id"] == user_standard.id
        assert "is_active" in data
        assert "role" not in data

        response = client_app.get(
            f"{API}{USERS}/{user_standard.id}",
            headers={"Authorization": f"Bearer {access_token_user_admin}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["id"] == user_standard.id
        assert "is_active" in data
        assert "role" in data


def test_get_user_fail(
    client_app,
    access_token_user_admin,
    access_token_user_moderator,
    access_token_user_standard,
):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{USERS}/-1",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        assert response.json()["detail"] == USER_NOT_FOUND


def test_update_user_success(
    session, client_app, access_token_user_moderator, user_in_moderator_json
):
    user_moderator = session.query(User).filter_by(email=EMAIL_MODERATOR).first()
    new_username = "new username"
    new_email = "new_test@email.com"
    user_in_moderator_json["username"] = new_username
    user_in_moderator_json["email"] = new_email
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.patch(
            f"{API}{USERS}/",
            json=user_in_moderator_json,
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["user"]["id"] == user_moderator.id
        assert data["user"]["username"] == new_username
        assert data["user"]["email"] == new_email
    user_moderator = session.query(User).filter_by(id=user_moderator.id).first()
    user_moderator.username = USERNAME_MODERATOR
    user_moderator.email = EMAIL_MODERATOR
    session.commit()


def test_update_user_fail_same_data(
    client_app, access_token_user_moderator, user_in_moderator_json
):
    user_in_moderator_json["username"] = USERNAME_STANDARD
    user_in_moderator_json["email"] = "new_test@email.com"
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.patch(
            f"{API}{USERS}/",
            json=user_in_moderator_json,
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT, response.text
        assert response.json()["detail"] == USERNAME_EXISTS

        user_in_moderator_json["username"] = "new username"
        user_in_moderator_json["email"] = EMAIL_STANDARD
        response = client_app.patch(
            f"{API}{USERS}/",
            json=user_in_moderator_json,
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT, response.text
        assert response.json()["detail"] == EMAIL_EXISTS



from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
from time import sleep

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import status

from src.schemas.tags import TagIn
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
    USER_NOT_FOUND,
    INVALID_SORT_TYPE,
    FORBIDDEN_FOR_NOT_OWNER,
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


def test_update_photo_success(
    session, client_app, photo, photo_in_json, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    photo_in_new_data = PhotoIn(**photo_in_json)
    photo_in_new_data.description = "new test description"
    photo_in_new_data.tags = [
        TagIn(name="new tag1 test"),
        TagIn(name="new tag2 test"),
    ]
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.patch(
            f"{API}{PHOTOS}/{photo.id}",
            json=photo_in_new_data.model_dump_json(),
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["id"] == photo.id
    assert data["description"] == "new test description"
    assert data["tags"][0]["name"] == "new tag1 test"
    assert data["tags"][1]["name"] == "new tag2 test"


def test_update_photo_fail_wrong_photo_id(
    session, client_app, photo, photo_in_json, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    photo_in_new_data = PhotoIn(**photo_in_json)
    photo_in_new_data.description = "new test description"
    photo_in_new_data.tags = [
        TagIn(name="new tag1 test"),
        TagIn(name="new tag2 test"),
    ]
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.patch(
            f"{API}{PHOTOS}/-1",
            json=photo_in_new_data.model_dump_json(),
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    assert response.json()["detail"] == PHOTO_NOT_FOUND


def test_update_photo_fail_not_owner(
    session, client_app, photo, photo_in_json, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    photo_in_new_data = PhotoIn(**photo_in_json)
    photo_in_new_data.description = "new test description"
    photo_in_new_data.tags = [
        TagIn(name="new tag1 test"),
        TagIn(name="new tag2 test"),
    ]
    photo.user_id = 999
    session.add(photo)
    session.commit()
    session.refresh(photo)
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.patch(
            f"{API}{PHOTOS}/{photo.id}",
            json=photo_in_new_data.model_dump_json(),
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
    assert response.json()["detail"] == FORBIDDEN_FOR_NOT_OWNER


def test_get_photos_all_no_query_success(
    session, client_app, photo, photo_2, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.add(photo_2)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == photo.id
    assert data[1]["id"] == photo_2.id


def test_get_photos_all_with_query_success(
    session, client_app, photo, photo_2, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.add(photo_2)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}?query=test",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == photo.id
    assert data[0]["description"] == photo.description


def test_get_photos_all_with_user_id_success(
    session, client_app, photo, photo_2, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.add(photo_2)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}?user_id=1",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == photo.id
    assert data[0]["description"] == photo.description


def test_get_photos_all_with_user_id_and_query_success(
    session, client_app, photo, photo_2, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.add(photo_2)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}?user_id=1&query=test",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == photo.id
    assert data[0]["description"] == photo.description


def test_get_photos_all_with_sort_by_success(
    session, client_app, photo, photo_2, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    sleep(1)
    session.add(photo_2)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}?sort_by=upload_date-desc",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == photo_2.id
    assert data[1]["id"] == photo.id

    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}?sort_by=upload_date-asc",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == photo.id
    assert data[1]["id"] == photo_2.id

    # add sort by rating tests


def test_get_photos_wrong_user_id_fail(
    session, client_app, photo, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}?user_id=999",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    assert response.json()["detail"] == USER_NOT_FOUND


def test_get_photos_wrong_sort_by_text_fail(
    session, client_app, photo, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}?sort_by=test",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_502_BAD_GATEWAY, response.text
    assert response.json()["detail"] == INVALID_SORT_TYPE

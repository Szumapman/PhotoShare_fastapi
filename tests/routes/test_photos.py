from unittest.mock import patch
from time import sleep

from fastapi import status

from src.schemas.tags import TagIn
from src.services.auth import auth_service
from src.database.models import User, Photo, Rating

from src.conf.constants import (
    API,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    PHOTO_NOT_FOUND,
    FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR,
    USER_NOT_FOUND,
    INVALID_SORT_TYPE,
    FORBIDDEN_FOR_NOT_OWNER,
    FORBIDDEN_FOR_OWNER,
    RATING_DELETED,
    RATING_NOT_FOUND,
    PHOTO_CREATED,
    PHOTO_DELETED,
    PHOTO_UPDATED,
    PHOTO_RATED,
)
from tests.routes.conftest import (
    EMAIL_STANDARD,
    PHOTO_URL,
    EMAIL_ADMIN,
    EMAIL_MODERATOR,
    TRANSFORM_PHOTO_URL,
    TRANSFORM_PARAMS,
)
from src.conf.constants import PHOTOS
from src.schemas.photos import PhotoIn


def test_create_photo_success(client_app, photo_in_json, access_token_user_standard):
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
        assert data["photo"]["photo_url"] == PHOTO_URL
        assert "id" in data["photo"]
        assert data["photo"]["description"] == photo_in_data.description
        assert data["photo"]["tags"][0]["name"] == photo_in_data.tags[0].name
        assert data["detail"] == PHOTO_CREATED


def test_get_photo_success(session, client_app, photo, access_token_user_standard):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}/{photo.id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["id"] == photo.id
    assert data["photo_url"] == PHOTO_URL


def test_get_photo_fail(session, client_app, access_token_user_standard):
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{PHOTOS}/{photo.id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["photo"]["id"] == photo.id
        assert data["detail"] == PHOTO_DELETED


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
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{PHOTOS}/{photo.id}",
            headers={"Authorization": f"Bearer {access_token_user_admin}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["photo"]["id"] == photo.id
        assert data["detail"] == PHOTO_DELETED


def test_delete_fail_wrong_user_id(
    session, client_app, photo, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    photo.user_id = 999
    session.add(photo)
    session.commit()
    session.refresh(photo)
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.patch(
            f"{API}{PHOTOS}/{photo.id}",
            json=photo_in_new_data.model_dump_json(),
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["photo"]["id"] == photo.id
    assert data["photo"]["description"] == "new test description"
    assert data["photo"]["tags"][0]["name"] == "new tag1 test"
    assert data["photo"]["tags"][1]["name"] == "new tag2 test"
    assert data["detail"] == PHOTO_UPDATED


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
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
    session, client_app, photo, photo_2, rating, rating_2, access_token_user_standard
):
    session.query(Photo).delete()
    session.query(Rating).delete()
    session.commit()
    session.add(photo)
    session.add(rating)
    session.add(rating_2)
    session.commit()
    sleep(1)
    session.add(photo_2)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
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

        response = client_app.get(
            f"{API}{PHOTOS}?sort_by=upload_date-asc",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == photo.id
        assert data[1]["id"] == photo_2.id

        response = client_app.get(
            f"{API}{PHOTOS}?sort_by=rating-desc",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data[0]["id"] == photo_2.id
        assert data[1]["id"] == photo.id

        response = client_app.get(
            f"{API}{PHOTOS}?sort_by=rating-asc",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data[0]["id"] == photo.id
        assert data[1]["id"] == photo_2.id


def test_get_photos_wrong_user_id_fail(
    session, client_app, photo, access_token_user_standard
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
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
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}?sort_by=test",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_502_BAD_GATEWAY, response.text
    assert response.json()["detail"] == INVALID_SORT_TYPE


def test_get_qr_code_success(
    session,
    client_app,
    photo,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}/{photo.id}/qr_code",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.headers["Content-Type"] == "image/png"


def test_get_qr_code_with_transform_id_success(
    session,
    client_app,
    photo,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    photo.transformations = {"1": ["transformed_url.jpg"]}
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}/{photo.id}/qr_code?transform_id=1",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.headers["Content-Type"] == "image/png"


def test_get_qr_code_with_invalid_transform_id_fail(
    session,
    client_app,
    photo,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    photo.transformations = {"1": ["transformed_url.jpg"]}
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}/{photo.id}/qr_code?transform_id=2",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "No data found for transformation id: 2"


def test_get_qr_code_with_invalid_photo_id_fail(
    session,
    client_app,
    photo,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{PHOTOS}/999/qr_code",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == PHOTO_NOT_FOUND


def test_transform_photo_success(
    session,
    client_app,
    photo,
    transform_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{PHOTOS}/{photo.id}/transform",
            json=transform_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["photo"]["id"] == photo.id
    assert data["photo"]["transformations"] == {
        "1": [TRANSFORM_PHOTO_URL, TRANSFORM_PARAMS]
    }
    assert data["detail"] == PHOTO_UPDATED


def test_transform_photo_with_invalid_photo_id_fail(
    session,
    client_app,
    photo,
    transform_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{PHOTOS}/999/transform",
            json=transform_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == PHOTO_NOT_FOUND


def test_transform_photo_not_owner_fail(
    session,
    client_app,
    photo,
    transform_in_json,
    access_token_user_admin,
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{PHOTOS}/{photo.id}/transform",
            json=transform_in_json,
            headers={"Authorization": f"Bearer {access_token_user_admin}"},
        )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == FORBIDDEN_FOR_NOT_OWNER


def test_transform_photo_invalid_transform_fail(
    session,
    client_app,
    photo,
    transform_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{PHOTOS}/{photo.id}/transform",
            json={
                "background": "blue",
                "aspect_ratio": "2:1",
                "gravity": "west",
                "angle": 30,
                "width": 0,
                "height": 200,
                "crop": "crop",
                "effects": ["error_effect"],
            },
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_rate_photo_success(
    session,
    client_app,
    photo_2,
    rating_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo_2)
    session.commit()
    session.refresh(photo_2)
    photo_2_id = photo_2.id
    user_id = 1
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{PHOTOS}/{photo_2_id}/rate",
            json=rating_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["rating"]["photo_id"] == photo_2_id
        assert data["rating"]["user_id"] == user_id
        assert data["rating"]["score"] == rating_in_json["score"]
        assert data["detail"] == PHOTO_RATED

        rating_in_json["score"] = 1
        response = client_app.post(
            f"{API}{PHOTOS}/{photo_2_id}/rate",
            json=rating_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["rating"]["photo_id"] == photo_2_id
        assert data["rating"]["user_id"] == user_id
        assert data["rating"]["score"] == rating_in_json["score"]
        assert data["detail"] == PHOTO_RATED


def test_rate_photo_with_invalid_photo_id_fail(
    client_app,
    rating_in_json,
    access_token_user_standard,
):

    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{PHOTOS}/999/rate",
            json=rating_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == PHOTO_NOT_FOUND


def test_rate_photo_with_invalid_score_fail(
    session,
    client_app,
    photo_2,
    rating_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo_2)
    session.commit()
    session.refresh(photo_2)
    photo_2_id = photo_2.id
    rating_in_json["score"] = 10
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{PHOTOS}/{photo_2_id}/rate",
            json=rating_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        rating_in_json["score"] = 0
        response = client_app.post(
            f"{API}{PHOTOS}/{photo_2_id}/rate",
            json=rating_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_rate_photo_by_owner_fail(
    session,
    client_app,
    photo,
    rating_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    session.refresh(photo)
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{PHOTOS}/{photo.id}/rate",
            json=rating_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == FORBIDDEN_FOR_OWNER


def test_delete_rating_success(
    session,
    client_app,
    photo_2,
    rating,
    rating_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.query(Rating).delete()
    session.commit()
    session.add(photo_2)
    session.add(rating)
    session.commit()
    photo_2_id = photo_2.id
    user_id = 1
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{PHOTOS}/{photo_2_id}/rate",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["rating"]["photo_id"] == photo_2_id
        assert data["rating"]["user_id"] == user_id
        assert data["rating"]["score"] == rating_in_json["score"]
        assert data["detail"] == RATING_DELETED


def test_delete_rating_with_invalid_photo_id_fail(
    client_app,
    access_token_user_standard,
):
    with patch.object(auth_service, "redis_connection") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{PHOTOS}/999/rate",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == RATING_NOT_FOUND

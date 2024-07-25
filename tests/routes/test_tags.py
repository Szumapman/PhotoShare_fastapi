from unittest.mock import patch

from fastapi import status

from src.services.auth import auth_service
from src.database.models import Tag

from src.conf.constants import (
    API,
    TAGS,
    TAG_CREATED,
    TAG_ALREADY_EXISTS,
    TAG_NOT_FOUND,
    TAG_UPDATED,
    TAG_DELETED,
    TAGS_GET_ENUM,
    FORBIDDEN_FOR_USER,
    FORBIDDEN_FOR_USER_AND_MODERATOR,
)


def test_create_tag_success(client_app, tag_in_json, access_token_user_standard):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{TAGS}/",
            json=tag_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_201_CREATED, response.text
        data = response.json()
        assert data["tag"]["name"] == tag_in_json["name"]
        assert data["detail"] == TAG_CREATED


def test_create_tag_fail_already_exists(
    session, client_app, tag, tag_in_json, access_token_user_standard
):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{TAGS}/",
            json=tag_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT, response.text
        data = response.json()
        assert data["detail"] == TAG_ALREADY_EXISTS


def test_get_tags_no_sort_success(
    session, client_app, tag, tag_2, access_token_user_standard
):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.add(tag_2)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{TAGS}/",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == tag.name
    assert data[1]["name"] == tag_2.name


def test_get_tags_sort_success(
    session, client_app, tag, tag_2, access_token_user_standard
):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.add(tag_2)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{TAGS}/?sort_by={TAGS_GET_ENUM[0]}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == tag.name
        assert data[1]["name"] == tag_2.name

        response = client_app.get(
            f"{API}{TAGS}/?sort_by={TAGS_GET_ENUM[1]}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == tag_2.name
        assert data[1]["name"] == tag.name


def test_get_tag_by_id_success(session, client_app, tag, access_token_user_standard):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{TAGS}/{tag.id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["name"] == tag.name
    assert data["id"] == tag.id


def test_get_tag_by_id_fail_not_found(
    session, client_app, tag, access_token_user_standard
):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{TAGS}/999",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    data = response.json()
    assert data["detail"] == TAG_NOT_FOUND


def test_update_tag_success(
    session,
    client_app,
    tag,
    tag_in_json,
    access_token_user_moderator,
    access_token_user_admin,
):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.commit()
    tag_in_json["name"] = "new_name"
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.put(
            f"{API}{TAGS}/{tag.id}",
            json=tag_in_json,
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["tag"]["name"] == tag_in_json["name"]
        assert data["tag"]["id"] == tag.id
        assert data["detail"] == TAG_UPDATED

        tag_in_json["name"] = "new_name_2"
        response = client_app.put(
            f"{API}{TAGS}/{tag.id}",
            json=tag_in_json,
            headers={"Authorization": f"Bearer {access_token_user_admin}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["tag"]["name"] == tag_in_json["name"]
        assert data["tag"]["id"] == tag.id
        assert data["detail"] == TAG_UPDATED


def test_update_tag_fail_not_found(
    session,
    client_app,
    tag,
    tag_in_json,
    access_token_user_moderator,
):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.commit()
    tag_in_json["name"] = "new_name"
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.put(
            f"{API}{TAGS}/999",
            json=tag_in_json,
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        assert data["detail"] == TAG_NOT_FOUND


def test_update_tag_fail_lack_of_permission(
    session,
    client_app,
    tag,
    tag_in_json,
    access_token_user_standard,
):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.commit()
    tag_in_json["name"] = "new_name"
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.put(
            f"{API}{TAGS}/{tag.id}",
            json=tag_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
        data = response.json()
        assert data["detail"] == FORBIDDEN_FOR_USER


def test_delete_tag_success(
    session,
    client_app,
    tag,
    access_token_user_admin,
):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{TAGS}/{tag.id}",
            headers={"Authorization": f"Bearer {access_token_user_admin}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["detail"] == TAG_DELETED
        assert data["tag"]["id"] == tag.id
        assert data["tag"]["name"] == tag.name


def test_delete_tag_fail_not_found(
    session,
    client_app,
    tag,
    access_token_user_admin,
):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{TAGS}/999",
            headers={"Authorization": f"Bearer {access_token_user_admin}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
        data = response.json()
        assert data["detail"] == TAG_NOT_FOUND


def test_delete_tag_fail_lack_of_permission(
    session,
    client_app,
    tag,
    access_token_user_standard,
    access_token_user_moderator,
):
    session.query(Tag).delete()
    session.commit()
    session.add(tag)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{TAGS}/{tag.id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
        data = response.json()
        assert data["detail"] == FORBIDDEN_FOR_USER_AND_MODERATOR

        response = client_app.delete(
            f"{API}{TAGS}/{tag.id}",
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
        data = response.json()
        assert data["detail"] == FORBIDDEN_FOR_USER_AND_MODERATOR

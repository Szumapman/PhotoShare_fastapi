from unittest.mock import patch

from fastapi import status

from src.database.models import Photo, Comment
from src.conf.constants import (
    API,
    COMMENTS,
    COMMENT_CREATED,
    PHOTO_NOT_FOUND,
    COMMENT_NOT_FOUND,
    COMMENT_UPDATED,
    FORBIDDEN_FOR_NOT_OWNER,
    COMMENT_DELETED,
    FORBIDDEN_FOR_USER,
)
from src.schemas.comments import CommentUpdate
from src.services.auth import auth_service


def test_create_comment_success(
    session,
    client_app,
    photo,
    comment_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    session.add(photo)
    session.commit()
    photo_id = photo.id
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{COMMENTS}/",
            json=comment_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["comment"]["content"] == comment_in_json["content"]
    assert data["comment"]["photo_id"] == photo_id
    assert data["comment"]["user_id"] == 1
    assert data["detail"] == COMMENT_CREATED


def test_create_comment_no_photo_fail(
    session,
    client_app,
    comment_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.post(
            f"{API}{COMMENTS}/",
            json=comment_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    data = response.json()
    assert data["detail"] == PHOTO_NOT_FOUND


def test_get_comments_success(
    session,
    client_app,
    photo,
    comment,
    comment_2,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.query(Comment).delete()
    session.commit()
    session.add(photo)
    session.add(comment)
    session.add(comment_2)
    session.commit()
    photo_id = photo.id
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{COMMENTS}/",
            params={"photo_id": photo_id},
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    print(data)
    assert len(data) == 2
    assert data[0]["content"] == comment.content
    assert data[0]["photo_id"] == photo_id
    assert data[0]["user_id"] == comment.user_id
    assert data[1]["content"] == comment_2.content
    assert data[1]["photo_id"] == photo_id
    assert data[1]["user_id"] == comment_2.user_id


def test_get_comments_no_photo_fail(
    session,
    client_app,
    comment,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.query(Comment).delete()
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{COMMENTS}/",
            params={"photo_id": 999},
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    data = response.json()
    assert data["detail"] == PHOTO_NOT_FOUND


def test_get_comment_success(
    session,
    client_app,
    photo,
    comment,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.query(Comment).delete()
    session.commit()
    session.add(photo)
    session.add(comment)
    session.commit()
    comment_id = comment.id
    photo_id = photo.id
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{COMMENTS}/{comment_id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["content"] == comment.content
    assert data["photo_id"] == photo_id
    assert data["user_id"] == comment.user_id


def test_get_comment_no_comment_fail(
    session,
    client_app,
    comment,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.query(Comment).delete()
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.get(
            f"{API}{COMMENTS}/{comment.id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    data = response.json()
    assert data["detail"] == COMMENT_NOT_FOUND


def test_update_comment_success(
    session,
    client_app,
    photo,
    comment,
    comment_update_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.query(Comment).delete()
    session.commit()
    session.add(photo)
    session.add(comment)
    session.commit()
    comment_id = comment.id
    photo_id = photo.id
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.patch(
            f"{API}{COMMENTS}/{comment_id}",
            json=comment_update_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["comment"]["content"] == comment_update_in_json["content"]
    assert data["comment"]["photo_id"] == photo_id
    assert data["comment"]["user_id"] == comment.user_id
    assert data["detail"] == COMMENT_UPDATED


def test_update_comment_no_comment_fail(
    session,
    client_app,
    comment,
    comment_update_in_json,
    access_token_user_standard,
):
    session.query(Photo).delete()
    session.query(Comment).delete()
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.patch(
            f"{API}{COMMENTS}/999",
            json=comment_update_in_json,
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    data = response.json()
    assert data["detail"] == COMMENT_NOT_FOUND


def test_update_comment_by_not_owner_fail(
    session,
    client_app,
    photo,
    comment,
    comment_update_in_json,
    access_token_user_moderator,
):
    session.query(Photo).delete()
    session.query(Comment).delete()
    session.commit()
    session.add(photo)
    session.add(comment)
    session.commit()
    comment_id = comment.id
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.patch(
            f"{API}{COMMENTS}/{comment_id}",
            json=comment_update_in_json,
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
    data = response.json()
    assert data["detail"] == FORBIDDEN_FOR_NOT_OWNER


def test_delete_comment_success(
    session,
    client_app,
    photo,
    comment,
    comment_2,
    access_token_user_moderator,
    access_token_user_admin,
):
    session.query(Photo).delete()
    session.query(Comment).delete()
    session.commit()
    session.add(photo)
    session.add(comment)
    session.add(comment_2)
    session.commit()
    comment_id = comment.id
    comment_2_id = comment_2.id
    comment_user_id = comment.user_id
    comment_2_user_id = comment_2.user_id
    comment_content = comment.content
    comment_2_content = comment_2.content
    photo_id = photo.id
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{COMMENTS}/{comment_id}",
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["comment"]["content"] == comment_content
        assert data["comment"]["photo_id"] == photo_id
        assert data["comment"]["user_id"] == comment_user_id
        assert data["detail"] == COMMENT_DELETED

        response = client_app.delete(
            f"{API}{COMMENTS}/{comment_2_id}",
            headers={"Authorization": f"Bearer {access_token_user_admin}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["comment"]["content"] == comment_2_content
        assert data["comment"]["photo_id"] == photo_id
        assert data["comment"]["user_id"] == comment_2_user_id
        assert data["detail"] == COMMENT_DELETED


def test_delete_comment_by_not_admin_or_moderator_fail(
    session, client_app, photo, comment, access_token_user_standard
):
    session.query(Photo).delete()
    session.query(Comment).delete()
    session.commit()
    session.add(photo)
    session.add(comment)
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{COMMENTS}/{comment.id}",
            headers={"Authorization": f"Bearer {access_token_user_standard}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
        data = response.json()
        assert data["detail"] == FORBIDDEN_FOR_USER


def test_delete_comment_no_comment_fail(
    session, client_app, access_token_user_moderator
):
    session.query(Photo).delete()
    session.query(Comment).delete()
    session.commit()
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        response = client_app.delete(
            f"{API}{COMMENTS}/999",
            headers={"Authorization": f"Bearer {access_token_user_moderator}"},
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    data = response.json()
    assert data["detail"] == COMMENT_NOT_FOUND

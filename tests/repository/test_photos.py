import unittest
from unittest.mock import AsyncMock, MagicMock, call, patch, Mock
from datetime import datetime

from sqlalchemy.orm import Session

from src.conf.errors import NotFoundError, ForbiddenError
from src.database.models import Tag, User, Photo
from src.schemas.photos import TagIn, PhotoIn
from src.repository.photos import PostgresPhotoRepo
from src.conf.constant import (
    ROLE_STANDARD,
    PHOTO_NOT_FOUND,
    FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR,
    ROLE_ADMIN,
    FORBIDDEN_FOR_NOT_OWNER,
)


class TestPostgresPhotoRepo(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.repo = PostgresPhotoRepo(self.db)
        self.photo_url = "https://example.com/photo.jpg"
        self.qr_code_url = "https://example.com/qr.png"
        self.tag1_in = TagIn(name="tag1")
        self.tag2_in = TagIn(name="tag2")
        self.tag1 = Tag(name="tag1")
        self.tag2 = Tag(name="tag2")
        self.photo_info = PhotoIn(
            description="Test photo", tags=[self.tag1_in, self.tag2_in]
        )
        self.user = User(
            id=1,
            username="test_user",
            email="test_user@email.com",
            password="P@ssw0rd!",
            role=ROLE_STANDARD,
            created_at=datetime(2024, 5, 15, 10, 00, 00, 00),
            avatar="test_avatar.jpg",
            is_active=True,
        )
        self.user_2 = User(
            id=2,
            username="test_user_2",
            email="test_user_2@email.com",
            password="P@ssw0rd!",
            role=ROLE_ADMIN,
            created_at=datetime(2024, 5, 15, 10, 00, 00, 00),
            avatar="test_avatar.jpg",
            is_active=True,
        )
        self.user_mock = MagicMock()
        self.user_mock.id = 1
        self.user_mock.username = "test_user"
        self.user_mock.email = "test_user@email.com"
        self.user_mock.password = "<PASSWORD>!"
        self.user_mock.role = ROLE_STANDARD
        self.user_mock.created_at = datetime(2024, 5, 15, 10, 00, 00, 00)
        self.user_mock.avatar = "test_avatar.jpg"
        self.user_mock.is_active = True

        self.photo = Photo(
            id=1,
            user_id=self.user.id,
            photo_url=self.photo_url,
            qr_url=self.qr_code_url,
            description=self.photo_info.description,
            tags=[self.tag1, self.tag2],
        )
        self.photo_2 = Photo(
            id=2,
            user_id=self.user_2.id,
            photo_url=self.photo_url,
            qr_url=self.qr_code_url,
            description=self.photo_info.description,
            tags=[self.tag1],
        )
        self.photo_mock = MagicMock()
        self.photo_mock.id = 1
        self.photo_mock.user_id = self.user_mock.id
        self.photo_mock.photo_url = self.photo_url
        self.photo_mock.qr_url = self.qr_code_url
        self.photo_mock.description = self.photo_info.description
        self.photo_mock.tags = [self.tag1, self.tag2]

    async def test_upload_photo_with_existing_tags(self):
        self.db.add(self.tag1)
        self.db.add(self.tag2)
        self.db.commit()

        new_photo = Photo(
            user_id=self.user.id,
            photo_url=self.photo_url,
            qr_url=self.qr_code_url,
            description=self.photo_info.description,
            tags=[self.tag1, self.tag2],
        )
        self.db.add.return_value = new_photo

        photo = await self.repo.upload_photo(
            self.user.id, self.photo_info, self.photo_url, self.qr_code_url
        )

        assert photo.user_id == self.user.id
        assert photo.photo_url == self.photo_url
        assert photo.qr_url == self.qr_code_url
        assert photo.description == "Test photo"
        assert len(photo.tags) == 2

    async def test_upload_photo_with_new_tags(self):
        new_photo = Photo(
            user_id=self.user.id,
            photo_url=self.photo_url,
            qr_url=self.qr_code_url,
            description=self.photo_info.description,
            tags=[self.tag1, self.tag2],
        )
        self.db.add.return_value = new_photo

        photo = await self.repo.upload_photo(
            self.user.id, self.photo_info, self.photo_url, self.qr_code_url
        )

        assert photo.user_id == self.user.id
        assert photo.photo_url == self.photo_url
        assert photo.qr_url == self.qr_code_url
        assert photo.description == "Test photo"
        assert len(photo.tags) == 2

    async def test_upload_photo_with_empty_tags(self):
        photo_info = PhotoIn(description="Test photo", tags=[])
        new_photo = Photo(
            user_id=self.user.id,
            photo_url=self.photo_url,
            qr_url=self.qr_code_url,
            description=self.photo_info.description,
            tags=[],
        )
        self.db.add.return_value = new_photo
        photo = await self.repo.upload_photo(
            self.user.id, photo_info, self.photo_url, self.qr_code_url
        )

        assert photo.user_id == self.user.id
        assert photo.photo_url == self.photo_url
        assert photo.qr_url == self.qr_code_url
        assert photo.description == "Test photo"
        assert len(photo.tags) == 0

    async def test_get_photo_by_id_success(self):
        photo = Photo(
            id=1,
            user_id=self.user.id,
            photo_url=self.photo_url,
            qr_url=self.qr_code_url,
            description=self.photo_info.description,
            tags=[self.tag1, self.tag2],
        )
        self.db.query.return_value.filter.return_value.first.return_value = photo
        photo_out = await self.repo.get_photo_by_id(1)
        assert photo_out.user_id == self.user.id
        assert photo_out.photo_url == self.photo_url
        assert photo_out.qr_url == self.qr_code_url
        assert photo_out.description == self.photo_info.description
        assert len(photo_out.tags) == 2

    async def test_get_photo_by_id_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.repo.get_photo_by_id(1)
        self.assertEqual(e.exception.detail, PHOTO_NOT_FOUND)

    async def test_delete_photo_success_user_is_owner(self):
        self.db.query.return_value.filter.return_value.first.side_effect = [
            self.user_mock,
            self.photo_mock,
        ]
        photo_deleted = await self.repo.delete_photo(
            self.photo_mock.id, self.user_mock.id
        )
        assert photo_deleted.id == self.photo_mock.id
        assert photo_deleted.user_id == self.user_mock.id

    async def test_delete_photo_success_user_is_admin(self):
        self.photo_mock.user_id = 999
        self.user_mock.role = ROLE_ADMIN
        self.db.query.return_value.filter.return_value.first.side_effect = [
            self.user_mock,
            self.photo_mock,
        ]
        photo_deleted = await self.repo.delete_photo(
            self.photo_mock.id, self.user_mock.id
        )
        assert photo_deleted.id == self.photo_mock.id

    async def test_delete_photo_fail_not_owner(self):
        self.user_mock.id = 999
        self.db.query.return_value.filter.return_value.first.side_effect = [
            self.user_mock,
            self.photo_mock,
        ]
        with self.assertRaises(ForbiddenError) as e:
            await self.repo.delete_photo(self.photo_mock.id, self.user_mock.id)
        self.assertEqual(e.exception.detail, FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR)

    async def test_delete_photo_fail_not_found(self):
        self.db.query.return_value.filter.return_value.first.side_effect = [
            self.user_mock,
            None,
        ]
        with self.assertRaises(NotFoundError) as e:
            await self.repo.delete_photo(self.photo_mock.id, self.user_mock.id)
        self.assertEqual(e.exception.detail, PHOTO_NOT_FOUND)

    async def test_update_photo_success(self):
        self.db.query.return_value.filter.return_value.first.return_value = (
            self.photo_mock
        )
        new_photo_no_tags = PhotoIn(
            description="New description",
        )
        photo_updated = await self.repo.update_photo(
            self.photo_mock.id,
            new_photo_no_tags,
            self.user_mock.id,
        )
        assert photo_updated.id == self.photo_mock.id
        assert photo_updated.user_id == self.user_mock.id
        assert photo_updated.description == new_photo_no_tags.description

        new_phot_with_tags = PhotoIn(
            description="New description 2",
            tags=[self.tag1_in, self.tag2_in],
        )
        photo_updated = await self.repo.update_photo(
            self.photo_mock.id,
            new_phot_with_tags,
            self.user_mock.id,
        )
        assert photo_updated.id == self.photo_mock.id
        assert photo_updated.user_id == self.user_mock.id
        assert photo_updated.description == new_phot_with_tags.description

    async def test_update_photo_fail_not_owner(self):
        self.user_mock.id = 999
        self.db.query.return_value.filter.return_value.first.return_value = (
            self.photo_mock
        )
        new_photo_no_tags = PhotoIn(
            description="New description",
        )
        with self.assertRaises(ForbiddenError) as e:
            await self.repo.update_photo(
                self.photo_mock.id,
                new_photo_no_tags,
                self.user_mock.id,
            )
        self.assertEqual(e.exception.detail, FORBIDDEN_FOR_NOT_OWNER)

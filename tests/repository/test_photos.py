import unittest
from unittest.mock import AsyncMock, MagicMock, call
from datetime import datetime

from sqlalchemy.orm import Session

from src.database.models import Tag, User, Photo
from src.schemas.photos import TagIn, PhotoIn
from src.repository.photos import PostgresPhotoRepo
from src.conf.constant import ROLE_STANDARD


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
        print(new_photo.tags)
        photo = await self.repo.upload_photo(
            self.user.id, photo_info, self.photo_url, self.qr_code_url
        )

        assert photo.user_id == self.user.id
        assert photo.photo_url == self.photo_url
        assert photo.qr_url == self.qr_code_url
        assert photo.description == "Test photo"
        assert len(photo.tags) == 0

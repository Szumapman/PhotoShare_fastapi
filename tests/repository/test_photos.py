import unittest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from sqlalchemy.orm import Session

from src.conf.errors import NotFoundError, ForbiddenError
from src.database.models import Tag, User, Photo, Rating
from src.schemas.photos import TagIn, PhotoIn, RatingIn
from src.repository.photos import PostgresPhotoRepo
from src.conf.constant import (
    ROLE_STANDARD,
    PHOTO_NOT_FOUND,
    FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR,
    ROLE_ADMIN,
    FORBIDDEN_FOR_NOT_OWNER,
    USER_NOT_FOUND,
    FORBIDDEN_FOR_OWNER,
    RATING_NOT_FOUND,
)


class TestPostgresPhotoRepo(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.repo = PostgresPhotoRepo(self.db)
        self.photo_url = "https://example.com/photo.jpg"
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
            transformations={},
            uploaded_at=datetime(year=2024, month=1, day=1),
            description=self.photo_info.description,
            tags=[Tag(id=1, name="tag_1"), Tag(id=2, name="tag_2")],
        )
        self.photo_2 = Photo(
            id=2,
            user_id=self.user_2.id,
            photo_url=self.photo_url,
            uploaded_at=datetime(year=2024, month=2, day=2),
            description="Another description",
            tags=[Tag(id=1, name="tag_1")],
        )
        self.photo_mock = MagicMock()
        self.photo_mock.id = 1
        self.photo_mock.user_id = self.user_mock.id
        self.photo_mock.photo_url = self.photo_url
        self.photo_mock.description = self.photo_info.description
        self.photo_mock.tags = [self.tag1, self.tag2]

        self.skip = 0
        self.limit = 10

        self.rating_in = RatingIn(score=5)
        self.rating = Rating(
            photo_id=self.photo.id, user_id=self.user_2.id, score=self.rating_in.score
        )

    async def test_upload_photo_with_existing_tags(self):
        self.db.add(self.tag1)
        self.db.add(self.tag2)
        self.db.commit()

        new_photo = Photo(
            user_id=self.user.id,
            photo_url=self.photo_url,
            description=self.photo_info.description,
            tags=[self.tag1, self.tag2],
        )
        self.db.add.return_value = new_photo

        photo = await self.repo.upload_photo(
            self.user.id, self.photo_info, self.photo_url
        )

        assert photo.user_id == self.user.id
        assert photo.photo_url == self.photo_url
        assert photo.description == "Test photo"
        assert len(photo.tags) == 2

    async def test_upload_photo_with_new_tags(self):
        new_photo = Photo(
            user_id=self.user.id,
            photo_url=self.photo_url,
            description=self.photo_info.description,
            tags=[self.tag1, self.tag2],
        )
        self.db.add.return_value = new_photo

        photo = await self.repo.upload_photo(
            self.user.id, self.photo_info, self.photo_url
        )

        assert photo.user_id == self.user.id
        assert photo.photo_url == self.photo_url
        assert photo.description == "Test photo"
        assert len(photo.tags) == 2

    async def test_upload_photo_with_empty_tags(self):
        photo_info = PhotoIn(description="Test photo", tags=[])
        new_photo = Photo(
            user_id=self.user.id,
            photo_url=self.photo_url,
            description=self.photo_info.description,
            tags=[],
        )
        self.db.add.return_value = new_photo
        photo = await self.repo.upload_photo(self.user.id, photo_info, self.photo_url)

        assert photo.user_id == self.user.id
        assert photo.photo_url == self.photo_url
        assert photo.description == "Test photo"
        assert len(photo.tags) == 0

    async def test_get_photo_by_id_success(self):
        photo = Photo(
            id=1,
            user_id=self.user.id,
            photo_url=self.photo_url,
            description=self.photo_info.description,
            tags=[self.tag1, self.tag2],
        )
        self.db.query.return_value.filter.return_value.first.return_value = photo
        photo_out = await self.repo.get_photo_by_id(1)
        assert photo_out.user_id == self.user.id
        assert photo_out.photo_url == self.photo_url
        assert photo_out.description == self.photo_info.description
        assert len(photo_out.tags) == 2

    async def test_get_photo_by_id_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.repo.get_photo_by_id(1)
        self.assertEqual(e.exception.detail, PHOTO_NOT_FOUND)

    async def test_delete_photo_success_user_is_owner(self):
        self.repo.get_photo_by_id = AsyncMock(return_value=self.photo_mock)
        photo_deleted = await self.repo.delete_photo(
            self.photo_mock.id, self.user_mock.id, self.user_mock.role
        )
        assert photo_deleted.id == self.photo_mock.id
        assert photo_deleted.user_id == self.user_mock.id

    async def test_delete_photo_success_user_is_admin(self):
        self.photo_mock.user_id = 999
        self.user_mock.role = ROLE_ADMIN
        self.repo.get_photo_by_id = AsyncMock(return_value=self.photo_mock)
        photo_deleted = await self.repo.delete_photo(
            self.photo_mock.id, self.user_mock.id, self.user_mock.role
        )
        assert photo_deleted.id == self.photo_mock.id

    async def test_delete_photo_fail_not_owner(self):
        self.user_mock.id = 999
        self.repo.get_photo_by_id = AsyncMock(return_value=self.photo_mock)
        with self.assertRaises(ForbiddenError) as e:
            await self.repo.delete_photo(
                self.photo_mock.id, self.user_mock.id, self.user_mock.role
            )
        self.assertEqual(e.exception.detail, FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR)

    async def test_update_photo_success(self):
        self.repo.get_photo_by_id = AsyncMock(return_value=self.photo_mock)
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
        self.repo.get_photo_by_id = AsyncMock(return_value=self.photo_mock)
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

    async def test_get_photos_all_success(self):
        self.db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.photo,
            self.photo_2,
        ]
        photos_out = await self.repo.get_photos(self.skip, self.limit)
        assert len(photos_out) == 2
        assert photos_out[0].id == self.photo.id
        assert photos_out[0].user_id == self.user.id
        assert photos_out[1].id == self.photo_2.id
        assert photos_out[1].user_id == self.user_2.id

    async def test_get_photos_with_query_success(self):
        self.db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.photo_2
        ]
        photos_out = await self.repo.get_photos(self.skip, self.limit, query="Another")
        assert len(photos_out) == 1
        assert photos_out[0].id == self.photo_2.id
        assert photos_out[0].description == self.photo_2.description

        self.db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.photo,
            self.photo_2,
        ]
        photos_out = await self.repo.get_photos(self.skip, self.limit, query="tag")
        assert len(photos_out) == 2

    async def test_get_photos_with_user_id_success(self):
        self.db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.photo_2
        ]
        photos_out = await self.repo.get_photos(
            self.skip, self.limit, user_id=self.user_2.id
        )
        assert len(photos_out) == 1
        assert photos_out[0].id == self.photo_2.id
        assert photos_out[0].user_id == self.user_2.id

    async def test_get_photos_with_user_id_and_query_success(self):
        self.db.query.return_value.filter.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.photo_2
        ]
        photos_out = await self.repo.get_photos(
            self.skip,
            self.limit,
            query="Another",
            user_id=self.user_2.id,
        )
        assert len(photos_out) == 1
        assert photos_out[0].id == self.photo_2.id
        assert photos_out[0].user_id == self.user_2.id
        assert photos_out[0].description == self.photo_2.description

    async def test_get_photos_with_user_id_as_zero_or_non_exist_fail(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.repo.get_photos(self.skip, self.limit, user_id=0)
        self.assertEqual(e.exception.detail, USER_NOT_FOUND)
        with self.assertRaises(NotFoundError) as e:
            await self.repo.get_photos(self.skip, self.limit, user_id=999)
        self.assertEqual(e.exception.detail, USER_NOT_FOUND)

    async def test_get_photos_with_sort_by_success(self):
        self.db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.photo_2,
            self.photo,
        ]
        photos_out = await self.repo.get_photos(
            self.skip, self.limit, sort_by="upload_date-desc"
        )
        assert len(photos_out) == 2
        assert photos_out[0].id == self.photo_2.id
        assert photos_out[1].id == self.photo.id

        self.db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.photo,
            self.photo_2,
        ]
        photos_out = await self.repo.get_photos(
            self.skip, self.limit, sort_by="upload_date-asc"
        )
        assert len(photos_out) == 2
        assert photos_out[0].id == self.photo.id
        assert photos_out[1].id == self.photo_2.id

        self.db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.photo_2,
            self.photo,
        ]
        photos_out = await self.repo.get_photos(
            self.skip, self.limit, sort_by="rating-desc"
        )
        print(photos_out)
        assert len(photos_out) == 2
        assert photos_out[0].id == self.photo_2.id
        assert photos_out[1].id == self.photo.id

        self.db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.photo,
            self.photo_2,
        ]
        photos_out = await self.repo.get_photos(
            self.skip, self.limit, sort_by="rating-asc"
        )
        print(photos_out)
        assert len(photos_out) == 2
        assert photos_out[0].id == self.photo.id
        assert photos_out[1].id == self.photo_2.id

    async def test_add_transform_photo_success(self):
        transform_params = ["param1", "param2"]
        transformation_url = "http://example.com/transformation"
        self.repo.get_photo_by_id = AsyncMock(return_value=self.photo)
        photo_with_transform = await self.repo.add_transform_photo(
            self.photo.id,
            transform_params,
            transformation_url,
        )
        self.repo.get_photo_by_id.assert_called_once_with(self.photo.id)
        self.assertEqual(len(photo_with_transform.transformations), 1)
        self.assertEqual(photo_with_transform.transformations[1][0], transformation_url)
        self.assertEqual(photo_with_transform.transformations[1][1], transform_params)

        transform_params_2 = ["param1", "param2", "param3"]
        transformation_url_2 = "http://example.com/transformation_2"
        photo_with_transform = await self.repo.add_transform_photo(
            self.photo.id,
            transform_params_2,
            transformation_url_2,
        )
        self.assertEqual(len(photo_with_transform.transformations), 2)
        self.assertEqual(
            photo_with_transform.transformations[2][0], transformation_url_2
        )
        self.assertEqual(photo_with_transform.transformations[2][1], transform_params_2)

    async def test_rate_photo_success(self):
        self.repo.get_photo_by_id = AsyncMock(return_value=self.photo)
        self.db.query.return_value.filter.return_value.first.return_value = None
        rating = await self.repo.rate_photo(
            self.photo.id, self.rating_in, self.user_2.id
        )
        assert rating.photo_id == self.photo.id
        assert rating.user_id == self.user_2.id
        assert rating.score == self.rating.score

        self.db.query.return_value.filter.return_value.first.return_value = self.rating
        self.rating.score = 1
        rating = await self.repo.rate_photo(
            self.photo.id, self.rating_in, self.user_2.id
        )
        assert rating.photo_id == self.photo.id
        assert rating.user_id == self.user_2.id
        assert rating.score == self.rating.score

    async def test_rate_photo_fail(self):
        self.repo.get_photo_by_id = AsyncMock(return_value=self.photo)
        self.rating.user_id = self.user.id
        self.db.query.return_value.filter.return_value.first.return_value = self.rating
        with self.assertRaises(ForbiddenError) as e:
            await self.repo.rate_photo(self.photo.id, self.rating_in, self.user.id)
            self.assertEqual(e.exception.detail, FORBIDDEN_FOR_OWNER)

    async def test_delete_rating_success(self):
        self.db.query.return_value.filter.return_value.first.return_value = self.rating
        rating = await self.repo.delete_rating(self.photo.id, self.user_2.id)
        assert rating.photo_id == self.photo.id
        assert rating.user_id == self.user_2.id
        assert rating.score == self.rating.score

    async def test_delete_rating_fail(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.repo.delete_rating(999, self.user_2.id)
            self.assertEqual(e.exception.detail, RATING_NOT_FOUND)

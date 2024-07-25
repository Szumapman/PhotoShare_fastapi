import unittest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.orm import Session

from src.repository.tags import PostgresTagRepo
from src.database.models import Tag
from src.schemas.tags import TagIn
from src.conf.constants import TAGS_GET_ENUM, TAG_NOT_FOUND, TAG_ALREADY_EXISTS
from src.conf.errors import NotFoundError, ConflictError


class TestPostgresTagRepo(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.repo = PostgresTagRepo(self.db)
        self.tag_in = TagIn(name="tag1")
        self.tag = Tag(id=1, name="tag1")
        self.tag_2_in = TagIn(name="tag2")
        self.tag_2 = Tag(id=2, name="tag2")

    async def test_get_tag_by_name_success(self):
        self.db.query.return_value.filter.return_value.first.return_value = self.tag
        tag = await self.repo.get_tag_by_name(self.tag_in.name)
        self.assertEqual(self.tag.name, tag.name)
        self.assertEqual(self.tag.id, tag.id)

    async def test_get_tag_by_name_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = await self.repo.get_tag_by_name("unexisting_tag")
        self.assertIsNone(result)

    async def test_create_tag_success(self):
        tag = await self.repo.create_tag(self.tag_in.name)
        self.assertEqual(self.tag.name, tag.name)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    async def test_get_tags_success(self):
        self.db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.tag,
            self.tag_2,
        ]
        tags = await self.repo.get_tags(None, 0, 10)
        self.assertEqual(2, len(tags))
        self.assertEqual(self.tag.name, tags[0].name)
        self.assertEqual(self.tag.id, tags[0].id)
        self.assertEqual(self.tag_2.name, tags[1].name)
        self.assertEqual(self.tag_2.id, tags[1].id)

    async def test_get_tags_sort_by_name_success(self):
        self.db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.tag,
            self.tag_2,
        ]
        tags = await self.repo.get_tags(TAGS_GET_ENUM[0], 0, 10)
        self.assertEqual(2, len(tags))
        self.assertEqual(self.tag.name, tags[0].name)
        self.assertEqual(self.tag.id, tags[0].id)
        self.assertEqual(self.tag_2.name, tags[1].name)
        self.assertEqual(self.tag_2.id, tags[1].id)

        self.db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            self.tag_2,
            self.tag,
        ]
        tags = await self.repo.get_tags(TAGS_GET_ENUM[1], 0, 10)
        self.assertEqual(2, len(tags))
        self.assertEqual(self.tag_2.name, tags[0].name)
        self.assertEqual(self.tag_2.id, tags[0].id)
        self.assertEqual(self.tag.name, tags[1].name)
        self.assertEqual(self.tag.id, tags[1].id)

    async def test_get_tag_by_id_success(self):
        self.db.query.return_value.filter.return_value.first.return_value = self.tag
        tag = await self.repo.get_tag_by_id(self.tag.id)
        self.assertEqual(self.tag.name, tag.name)
        self.assertEqual(self.tag.id, tag.id)

    async def test_get_tag_by_id_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.repo.get_tag_by_id(self.tag.id)
        self.assertEqual(e.exception.detail, TAG_NOT_FOUND)

    async def test_update_tag_success(self):
        new_tag_name = "new_tag_name"
        self.tag.name = new_tag_name
        self.repo.get_tag_by_id = AsyncMock(return_value=self.tag)
        self.repo.get_tag_by_name = AsyncMock(return_value=None)
        tag = await self.repo.update_tag(self.tag.id, new_tag_name)
        self.assertEqual(self.tag.name, tag.name)
        self.assertEqual(self.tag.id, tag.id)
        self.db.commit.assert_called_once()

    async def test_update_tag_name_already_exists(self):
        new_tag_name = "tag2"
        self.tag.name = new_tag_name
        self.repo.get_tag_by_id = AsyncMock(return_value=self.tag)
        self.repo.get_tag_by_name = AsyncMock(return_value=self.tag_2)
        with self.assertRaises(ConflictError) as e:
            await self.repo.update_tag(self.tag.id, new_tag_name)
        self.assertEqual(e.exception.detail, TAG_ALREADY_EXISTS)

    async def test_delete_tag_success(self):
        self.repo.get_tag_by_id = AsyncMock(return_value=self.tag)
        tag = await self.repo.delete_tag(self.tag.id)
        self.assertEqual(self.tag.name, tag.name)
        self.assertEqual(self.tag.id, tag.id)
        self.db.delete.assert_called_once_with(self.tag)
        self.db.commit.assert_called_once()

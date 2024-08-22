import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from src.conf.constants import (
    COMMENT_NOT_FOUND,
    FORBIDDEN_FOR_NOT_OWNER,
)
from src.conf.errors import NotFoundError, ForbiddenError
from src.repository.comments import PostgresCommentRepo
from src.database.models import Comment


class TestPostgresCommentRepo(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.repo = PostgresCommentRepo(self.db)
        self.comment_content = "Test comment"
        self.comment_content_2 = "Test comment 2"
        self.comment_id = 1
        self.comment_id_2 = 2
        self.photo_id = 1
        self.photo_id_2 = 2
        self.user_id = 1
        self.user_id_2 = 2
        self.comment = Comment(
            id=self.comment_id,
            content=self.comment_content,
            photo_id=self.photo_id,
            user_id=self.user_id,
        )
        self.comment_2 = Comment(
            id=self.comment_id_2,
            content=self.comment_content_2,
            photo_id=self.photo_id,
            user_id=self.user_id_2,
        )

    async def test_create_comment_success(self):
        comment = await self.repo.create_comment(
            self.comment_content, self.photo_id, self.user_id
        )
        self.assertEqual(self.comment.content, comment.content)
        self.assertEqual(self.comment.photo_id, comment.photo_id)
        self.assertEqual(self.comment.user_id, comment.user_id)

    async def test_get_comments_success(self):
        self.db.query.return_value.filter.return_value.all.return_value = [
            self.comment,
            self.comment_2,
        ]
        comments = await self.repo.get_comments(self.photo_id)
        print(comments)
        self.assertEqual(self.comment.content, comments[0].content)
        self.assertEqual(self.comment_2, comments[1])

    async def test_get_comment_by_id_success(self):
        self.db.query.return_value.filter.return_value.first.return_value = self.comment
        comment = await self.repo.get_comment_by_id(self.comment_id)
        self.assertEqual(self.comment.content, comment.content)
        self.assertEqual(self.comment.photo_id, comment.photo_id)
        self.assertEqual(self.comment.user_id, comment.user_id)

    async def test_get_comment_by_id_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.repo.get_comment_by_id(999)
        self.assertEqual(e.exception.detail, COMMENT_NOT_FOUND)

    async def test_update_comment_success(self):
        new_comment_content = "New comment content"
        self.db.query.return_value.filter.return_value.first.return_value = self.comment
        comment = await self.repo.update_comment(
            self.comment_id, self.user_id, new_comment_content
        )
        self.assertEqual(new_comment_content, comment.content)
        self.assertEqual(self.comment.photo_id, comment.photo_id)
        self.assertEqual(self.comment.user_id, comment.user_id)

    async def test_update_comment_not_found(self):
        new_comment_content = "New comment content"
        self.db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.repo.update_comment(999, self.user_id, new_comment_content)
        self.assertEqual(e.exception.detail, COMMENT_NOT_FOUND)

    async def test_update_comment_not_owner(self):
        new_comment_content = "New comment content"
        self.db.query.return_value.filter.return_value.first.return_value = self.comment
        with self.assertRaises(ForbiddenError) as e:
            await self.repo.update_comment(
                self.comment_id, self.user_id_2, new_comment_content
            )
        self.assertEqual(e.exception.detail, FORBIDDEN_FOR_NOT_OWNER)

    async def test_delete_comment_success(self):
        self.db.query.return_value.filter.return_value.first.return_value = self.comment
        comment = await self.repo.delete_comment(self.comment_id)
        self.assertEqual(self.comment.content, comment.content)
        self.assertEqual(self.comment.photo_id, comment.photo_id)
        self.assertEqual(self.comment.user_id, comment.user_id)

    async def test_delete_comment_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.repo.delete_comment(999)
        self.assertEqual(e.exception.detail, COMMENT_NOT_FOUND)

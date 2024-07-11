import unittest
from unittest.mock import MagicMock
from datetime import datetime

from sqlalchemy.orm import Session

from src.conf.errors import NotFoundError
from src.repository.users import PostgresUserRepo
from src.database.models import User
from src.conf.constant import ROLE_ADMIN, ROLE_STANDARD, ROLE_MODERATOR, USER_NOT_FOUND
from src.schemas.users import UserIn


class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.user_repo = PostgresUserRepo(self.db)
        self.email_admin = "admin@email.com"
        self.email_moderator = "moderator@email.com"
        self.email_standard = "standard@email.com"
        self.avatar = "test_avatar.jpg"
        self.user_admin = User(
            id=1,
            username="test_name",
            email=self.email_admin,
            password="<PASSWORD>",
            role=ROLE_ADMIN,
            created_at=datetime(2024, 5, 15, 10, 00, 00, 00),
            avatar=self.avatar,
            is_active=True,
        )
        self.user_moderator = User(
            id=2,
            username="test_name",
            email=self.email_moderator,
            password="<PASSWORD>",
            role=ROLE_MODERATOR,
            created_at=datetime(2024, 5, 15, 10, 00, 00, 00),
            avatar=self.avatar,
            is_active=True,
        )
        self.user_standard = User(
            id=3,
            username="test_name",
            email=self.email_standard,
            password="<PASSWORD>",
            role=ROLE_STANDARD,
            created_at=datetime(2024, 5, 15, 10, 00, 00, 00),
            avatar=self.avatar,
            is_active=True,
        )
        self.new_user_in = UserIn(
            username="new name",
            email="new@email.com",
            password="P@ssword1",
        )

    async def test_get_user_by_email_success(self):
        self.db.query().filter().first.return_value = self.user_admin
        result = await self.user_repo.get_user_by_email(self.email_admin)
        self.assertEqual(result, self.user_admin)

    async def test_get_user_by_email_fail(self):
        self.db.query().filter().first.return_value = None
        result = await self.user_repo.get_user_by_email("wrong@email.com")
        self.assertIsNone(result)

    async def test_get_user_by_username_success(self):
        self.db.query().filter().first.return_value = self.user_admin
        result = await self.user_repo.get_user_by_username(self.user_admin.username)
        self.assertEqual(result, self.user_admin)

    async def test_get_user_by_username_fail(self):
        self.db.query().filter().first.return_value = None
        result = await self.user_repo.get_user_by_username("wrong name")
        self.assertIsNone(result)

    async def test_get_user_by_id_success(self):
        self.db.query().filter().first.return_value = self.user_admin
        result = await self.user_repo.get_user_by_id(self.user_admin.id)
        self.assertEqual(result, self.user_admin)

    async def test_get_user_by_id_fail(self):
        self.db.query().filter().first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.user_repo.get_user_by_id(999)
        self.assertEqual(e.exception.detail, USER_NOT_FOUND)

    async def test_get_users_success(self):
        self.db.query().all.return_value = [
            self.user_admin,
            self.user_moderator,
            self.user_standard,
        ]
        result = await self.user_repo.get_users()
        self.assertEqual(
            result, [self.user_admin, self.user_moderator, self.user_standard]
        )
        self.db.query().all.return_value = []
        result = await self.user_repo.get_users()
        self.assertEqual(result, [])

    async def test_create_user_success(self):

        result = await self.user_repo.create_user(
            self.new_user_in,
            self.avatar,
        )
        self.assertEqual(result.username, self.new_user_in.username)
        self.assertEqual(result.email, self.new_user_in.email)
        self.assertEqual(result.avatar, self.avatar)
        self.assertEqual(result.role, ROLE_STANDARD)
        self.assertIsInstance(result, User)

    async def test_update_user_success(self):
        self.db.query().filter().first.return_value = self.user_admin
        result = await self.user_repo.update_user(
            self.new_user_in,
            self.user_admin.id,
        )
        self.assertEqual(result.username, self.new_user_in.username)
        self.assertEqual(result.email, self.new_user_in.email)
        self.assertEqual(result.role, self.user_admin.role)
        self.assertIsInstance(result, User)

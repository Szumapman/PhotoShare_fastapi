import unittest
from unittest.mock import MagicMock
from datetime import datetime

from sqlalchemy.orm import Session

from src.repository.users import PostgresUserRepo
from src.database.models import User
from src.conf.constant import ROLE_ADMIN, ROLE_STANDARD, ROLE_MODERATOR


class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.user_repo = PostgresUserRepo(self.db)
        self.email_admin = "admin@email.com"
        self.email_moderator = "moderator@email.com"
        self.email_standard = "standard@email.com"
        self.user_admin = User(
            id=1,
            username="test_name",
            email=self.email_admin,
            password="<PASSWORD>",
            role=ROLE_ADMIN,
            created_at=datetime(2024, 5, 15, 10, 00, 00, 00),
            avatar="test_avatar.jpg",
            is_active=True,
        )

    async def test_get_user_by_email_success(self):
        self.db.query().filter().first.return_value = self.user_admin
        result = await self.user_repo.get_user_by_email(self.email_admin)
        self.assertEqual(result, self.user_admin)

    async def test_get_user_by_email_fail(self):
        self.db.query().filter().first.return_value = None
        result = await self.user_repo.get_user_by_email(self.email_admin)
        self.assertIsNone(result)

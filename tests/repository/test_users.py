import unittest
from unittest.mock import MagicMock
from datetime import datetime

from sqlalchemy.orm import Session

from src.conf.errors import NotFoundError, ForbiddenError
from src.repository.users import PostgresUserRepo
from src.database.models import User, RefreshToken, LogoutAccessToken
from src.conf.constant import (
    ROLE_ADMIN,
    ROLE_STANDARD,
    ROLE_MODERATOR,
    USER_NOT_FOUND,
    TOKEN_NOT_FOUND,
    FORBIDDEN_OPERATION_ON_ADMIN_ACCOUNT,
)
from src.schemas.users import UserIn, ActiveStatus, UserRoleIn


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
        self.refresh_token = RefreshToken(
            id=1,
            refresh_token="token",
            user_id=self.user_standard.id,
            session_id="session_id",
            expires_at=datetime(2024, 5, 15, 10, 15, 00, 00),
        )
        self.logout_access_token = LogoutAccessToken(
            id=1,
            logout_access_token="logout_access_token",
            expires_at=datetime(2024, 5, 15, 10, 15, 00, 00),
        )
        self.active_status = ActiveStatus(is_active=False)
        self.user_role_in = UserRoleIn(role=ROLE_MODERATOR)

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
        self.db.query().offset.return_value.limit.return_value.all.return_value = [
            self.user_admin,
            self.user_moderator,
            self.user_standard,
        ]
        result = await self.user_repo.get_users(0, 10)
        print(result)
        self.assertEqual(
            result, [self.user_admin, self.user_moderator, self.user_standard]
        )
        self.db.query().offset.return_value.limit.return_value.all.return_value = []
        result = await self.user_repo.get_users(0, 10)
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

    async def test_update_user_fail(self):
        self.db.query().filter().first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.user_repo.update_user(
                self.new_user_in,
                999,
            )
        self.assertEqual(e.exception.detail, USER_NOT_FOUND)

    async def test_update_user_avatar_success(self):
        new_avatar_url = "new_avatar_url"
        self.db.query().filter().first.return_value = self.user_standard
        result = await self.user_repo.update_user_avatar(
            self.user_standard.id, new_avatar_url
        )
        self.assertEqual(result.avatar, new_avatar_url)
        self.assertEqual(result.username, self.user_standard.username)
        self.assertIsInstance(result, User)

    async def test_update_user_avatar_fail(self):
        new_avatar_url = "new_avatar_url"
        self.db.query().filter().first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.user_repo.update_user_avatar(999, new_avatar_url)
        self.assertEqual(e.exception.detail, USER_NOT_FOUND)

    async def test_delete_user_success(self):
        self.db.query().filter().first.return_value = self.user_standard
        result = await self.user_repo.delete_user(self.user_standard.id)
        self.assertEqual(result, self.user_standard)

    async def test_delete_user_fail(self):
        self.db.query().filter().first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.user_repo.delete_user(999)
        self.assertEqual(e.exception.detail, USER_NOT_FOUND)

    async def test_add_refresh_token_success(self):
        result = await self.user_repo.add_refresh_token(
            1, "refresh_token", datetime.utcnow(), "session_id"
        )
        self.assertEqual(result, None)

    async def test_delete_refresh_token_success(self):
        self.db.query().filter().first.return_value = self.refresh_token
        result = await self.user_repo.delete_refresh_token(
            self.refresh_token.refresh_token, self.user_admin.id
        )
        self.assertEqual(result, None)

    async def test_delete_refresh_token_fail(self):
        self.db.query().filter().first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.user_repo.delete_refresh_token("wrong_token", self.user_admin.id)
        self.assertEqual(e.exception.detail, TOKEN_NOT_FOUND)

    async def test_logout_user_success(self):
        self.db.query().filter().first.return_value = self.refresh_token
        result = await self.user_repo.logout_user(
            self.refresh_token.refresh_token,
            self.refresh_token.session_id,
            self.user_standard,
        )
        self.assertEqual(result, self.user_standard)

    async def test_logout_user_fail(self):
        self.db.query().filter().first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.user_repo.logout_user(
                "wrong_token",
                "wrong_session_id",
                self.user_standard,
            )
        self.assertEqual(e.exception.detail, TOKEN_NOT_FOUND)

    async def test_is_user_logout(self):
        self.db.query().filter().first.return_value = self.logout_access_token
        result = await self.user_repo.is_user_logout(
            self.logout_access_token.logout_access_token
        )
        self.assertEqual(result, self.logout_access_token)

        self.db.query().filter().first.return_value = None
        result = await self.user_repo.is_user_logout("wrong_token")
        self.assertEqual(result, None)

    async def test_set_user_active_status_success(self):
        self.db.query().filter().first.return_value = self.user_standard
        result = await self.user_repo.set_user_active_status(
            self.user_standard.id,
            self.active_status,
            self.user_moderator,
        )
        self.assertEqual(result, self.user_standard)
        self.assertEqual(result.is_active, False)

    async def test_set_user_active_status_fail(self):
        self.db.query().filter().first.return_value = None
        with self.assertRaises(NotFoundError) as e:
            await self.user_repo.set_user_active_status(
                999,
                self.active_status,
                self.user_moderator,
            )
        self.assertEqual(e.exception.detail, USER_NOT_FOUND)

    async def test_set_user_active_status_fail_for_admin_user_carry_out_by_moderator(
        self,
    ):
        self.db.query().filter().first.return_value = self.user_admin
        with self.assertRaises(ForbiddenError) as e:
            await self.user_repo.set_user_active_status(
                self.user_admin.id,
                self.active_status,
                self.user_moderator,
            )
        self.assertEqual(e.exception.detail, FORBIDDEN_OPERATION_ON_ADMIN_ACCOUNT)

    async def test_set_user_role_success(self):
        self.db.query().filter().first.return_value = self.user_standard
        result = await self.user_repo.set_user_role(
            self.user_standard.id,
            self.user_role_in,
        )
        self.assertEqual(result, self.user_standard)
        self.assertEqual(result.role, ROLE_MODERATOR)

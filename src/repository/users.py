from datetime import datetime, timedelta
from typing import Type

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.repository.abstract import AbstractUserRepo
from src.schemas.users import UserIn, ActiveStatus, UserRoleIn
from src.database.models import User, RefreshToken, LogoutAccessToken
from src.conf.constants import (
    TOKEN_NOT_FOUND,
    ACCESS_TOKEN_EXPIRE,
    USER_NOT_FOUND,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_STANDARD,
    FORBIDDEN_OPERATION_ON_ADMIN_ACCOUNT,
)
from src.conf.errors import NotFoundError, ForbiddenError


class PostgresUserRepo(AbstractUserRepo):
    """
    This class is an implementation of the AbstractUserRepo interface to use with the PostgreSQL database.
    """

    def __init__(self, db: Session):
        """
        Constructor.
        :param db: sqlalchemy.orm.Session
        """
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Returns user from database based on provided email

        :param email: email of user to get from database
        :type email: str
        :return: user from database or None if user not found
        :rtype: User | None
        """
        return self.db.query(User).filter(User.email == email).first()

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Returns user from database based on provided username

        :param username: username of user to get from database
        :type username: str
        :return: user from database or None if user not found
        :rtype: User | None
        """
        return self.db.query(User).filter(User.username == username).first()

    async def get_user_by_id(self, user_id: int) -> User:
        """
        Returns user from database based on provided user id

        :param user_id: user id of user to get from database
        :type user_id: int
        :return: user from database
        :rtype: User
        :raise: NotFoundError: if user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise NotFoundError(detail=USER_NOT_FOUND)
        return user

    async def get_users(self, skip, limit) -> list[Type[User]]:
        """
        Returns users from database

        :param skip: number of users to skip
        :type skip: int
        :param limit: number of users to return
        :type limit: int
        :return: list of users
        :rtype: list[User]
        """
        return self.db.query(User).offset(skip).limit(limit).all()

    async def create_user(self, user: UserIn, avatar: str) -> User:
        """
        Creates new user in database

        :param user: user data to create
        :type user: UserIn
        :param avatar: avatar url
        :type avatar: str
        :return: created user
        :rtype: User
        """
        new_user = User(
            username=user.username,
            email=user.email,
            password=user.password,
            role=ROLE_STANDARD,
            avatar=avatar,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    async def create_admin(
        self, name: str, email: str, hashed_password: str, avatar: str
    ) -> User:
        """
        Creates new admin user in database

        This method should be used only locally, f.e. with manage.py file.

        :param name: new admin name
        :type name: str
        :param email: admin email
        :type email: str
        :param hashed_password: hashed password
        :type hashed_password: str
        :param avatar: avatar url
        :type avatar: str
        :return: created admin
        :rtype: User
        """
        new_admin = User(
            username=name,
            email=email,
            password=hashed_password,
            role=ROLE_ADMIN,
            avatar=avatar,
        )
        self.db.add(new_admin)
        self.db.commit()
        self.db.refresh(new_admin)
        return new_admin

    async def update_user(self, new_user_data: UserIn, user_id: int) -> User:
        """
        Updates user in database

        :param new_user_data: new user data
        :type new_user_data: UserIn
        :param user_id: id of user to update
        :type user_id: int
        :return: updated user
        :rtype: User
        """
        user = await self.get_user_by_id(user_id)
        user.username = new_user_data.username
        user.email = new_user_data.email
        user.password = new_user_data.password
        self.db.commit()
        self.db.refresh(user)
        return user

    async def update_user_avatar(self, user_id: int, new_avatar_url: str) -> User:
        """
        Updates user avatar in database

        :param user_id: id of user to update avatar
        :type user_id: int
        :param new_avatar_url: new avatar url
        :type new_avatar_url: str
        :return: updated user
        :rtype: User
        """
        user = await self.get_user_by_id(user_id)
        user.avatar = new_avatar_url
        self.db.commit()
        self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> User:
        """
        Deletes user from database

        :param user_id: id of user to delete
        :type user_id: int
        :return: deleted user
        :rtype: User
        """
        user = await self.get_user_by_id(user_id)
        self.db.delete(user)
        self.db.commit()
        return user

    async def add_refresh_token(
        self,
        user_id: int,
        token: str | None,
        expiration_date: datetime,
        session_id: str,
    ) -> None:
        """
        Adds refresh token to database

        :param user_id: id of user to add refresh token
        :type user_id: int
        :param token: refresh token
        :type token: str
        :param expiration_date: expiration date of refresh token
        :type expiration_date: datetime
        :param session_id: id of current session
        :type session_id: str
        :return: None
        """
        refresh_token = RefreshToken(
            refresh_token=token,
            user_id=user_id,
            session_id=session_id,
            expires_at=expiration_date,
        )
        self.db.add(refresh_token)
        self.db.commit()

    async def delete_refresh_token(self, token: str, user_id: int) -> None:
        """
        Deletes refresh token from database

        :param token: token to delete
        :type token: str
        :param user_id: id of user who token belongs to
        :type user_id: int
        :return: None
        """
        old_token = (
            self.db.query(RefreshToken)
            .filter(
                and_(
                    RefreshToken.refresh_token == token, RefreshToken.user_id == user_id
                )
            )
            .first()
        )
        if old_token is None:
            raise NotFoundError(detail=TOKEN_NOT_FOUND)
        self.db.delete(old_token)
        self.db.commit()

    async def logout_user(self, token: str, session_id: str, user: User) -> User:
        """
        Saves user logout data in database

        :param token: user refresh token to save
        :type token: str
        :param session_id: current session id to save
        :type session_id: str
        :param user: user to logout
        :return: logged-out user
        """
        refresh_token = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.session_id == session_id, RefreshToken.user_id == user.id
            )
            .first()
        )
        if refresh_token is None:
            raise NotFoundError(detail=TOKEN_NOT_FOUND)
        self.db.delete(refresh_token)
        logout_access_token = LogoutAccessToken(
            logout_access_token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE),
        )
        self.db.add(logout_access_token)
        self.db.commit()
        return user

    async def is_user_logout(self, token: str) -> bool:
        """
        Checks if user is logged out

        :param token: user refresh token to check
        :type token: str
        :return: LogoutAccessToken if user is logged out (means True), None otherwise (means False)
        :rtype: bool
        """
        return (
            self.db.query(LogoutAccessToken)
            .filter(LogoutAccessToken.logout_access_token == token)
            .first()
        )

    async def set_user_active_status(
        self, user_id: int, active_status: ActiveStatus, current_user: User
    ) -> User:
        """
        Sets user active status in database
        :param user_id: user id to set active status
        :type user_id: int
        :param active_status: new active status
        :type active_status: ActiveStatus
        :param current_user: user who performed action
        :return: updated user
        :rtype: User
        :raise: ForbiddenError: if user role is moderator and tries to change active status of admin account
        """
        user = await self.get_user_by_id(user_id)
        if user.role == ROLE_ADMIN and current_user.role == ROLE_MODERATOR:
            raise ForbiddenError(detail=FORBIDDEN_OPERATION_ON_ADMIN_ACCOUNT)
        user.is_active = active_status.is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    async def set_user_role(self, user_id: int, role: UserRoleIn) -> User:
        """
        Sets user role in database
        :param user_id: user id to set role
        :type user_id: int
        :param role: new role
        :type role: UserRoleIn
        :return: updated user
        :rtype: User
        """
        user = await self.get_user_by_id(user_id)
        user.role = role.role
        self.db.commit()
        self.db.refresh(user)
        return user

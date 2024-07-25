import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict

from src.conf.constants import (
    MAX_USERNAME_LENGTH,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_STANDARD,
)


class UserRoleEnum(str, Enum):
    """
    Enum for user roles.
    """

    admin = ROLE_ADMIN
    moderator = ROLE_MODERATOR
    standard = ROLE_STANDARD


class UserRoleInEnum(str, Enum):
    """
    Enum for user roles when creating new user or changing role remotely.
    """

    moderator = ROLE_MODERATOR
    standard = ROLE_STANDARD


class UserRoleIn(BaseModel):
    """
    Model for changing user role remotely.

    :param role: role of user
    :type role: UserRoleInEnum
    """

    role: UserRoleInEnum


class UserIn(BaseModel):
    """
    Model for creating / updating user.

    :param username: username of user
    :type username: str
    :param email: email of user
    :type email: EmailStr
    :param password: password of user
    :type password: str
    """

    username: str = Field(
        min_length=3, max_length=MAX_USERNAME_LENGTH, default="user name"
    )
    email: EmailStr = Field(max_length=150, default="user@example.com")
    password: str = Field(min_length=8, max_length=45, default="password")

    @field_validator("password")
    def validate_password(cls, password: str) -> str:
        """
        Validate password.

        :param password: password to validate
        :return: password
        :raise: ValueError if password is not valid
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        elif len(password) > 45:
            raise ValueError("Password must be less than 45 characters")
        elif not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*\W).{8,45}$", password):
            raise ValueError(
                "Password must contain at least one uppercase and lowercase letter, one digit and one special character"
            )
        return password


class UserDb(BaseModel):
    """
    Model for returning user from database.

    :param id: id of user
    :type id: int
    :param username: username of user
    :type username: str
    :param email: email of user
    :type email: EmailStr
    :param role: role of user
    :type role: UserRoleEnum
    :param created_at: date and time when user was created
    :type created_at: datetime
    :param avatar: url of user avatar
    :type avatar: str
    :param is_active: is user active
    :type is_active: bool
    """

    id: int
    username: str
    email: EmailStr
    role: UserRoleEnum
    created_at: datetime
    avatar: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    """
    Model for returning user public data.

    :param id: id of user
    :type id: int
    :param username: username of user
    :type username: str
    :param created_at: date and time when user was created
    :type created_at: datetime
    :param avatar: url of user avatar
    :type avatar: str
    """

    id: int
    username: str
    created_at: datetime
    avatar: str

    model_config = ConfigDict(from_attributes=True)


class UserModeratorView(UserPublic):
    """
    Model for returning user public data for moderators. Inherits from UserPublic.

    :param is_active: is user active
    :type is_active: bool
    """

    is_active: bool


class UserInfo(BaseModel):
    """
    Model for returning info about performed operation and user.

    :param user: user to whom the operation performed
    :type user: UserDb
    :param detail: detail of performed operation
    :type detail: str
    """

    user: UserDb
    detail: str


class TokenModel(BaseModel):
    """
    Model for returning access and refresh tokens.

    :param access_token: access token
    :type access_token: str
    :param refresh_token: refresh token
    :type refresh_token: str
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ActiveStatus(BaseModel):
    """
    Model for setting active status.

    :param is_active: user active status - True - active or False - banned
    :type is_active: bool
    """

    is_active: bool

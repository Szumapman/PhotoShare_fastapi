import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, field_validator

from src.conf.constant import (
    MAX_USERNAME_LENGTH,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_STANDARD,
)


class UserRoleEnum(str, Enum):
    admin = ROLE_ADMIN
    moderator = ROLE_MODERATOR
    standard = ROLE_STANDARD


class UserIn(BaseModel):
    username: str = Field(
        min_length=3, max_length=MAX_USERNAME_LENGTH, default="user name"
    )
    email: EmailStr = Field(max_length=150, unique=True, default="user@example.com")
    password: str = Field(min_length=8, max_length=45, default="password")

    @field_validator("password")
    def validate_password(cls, password: str) -> str:
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
    id: int
    username: str
    email: EmailStr
    role: UserRoleEnum
    created_at: datetime
    avatar: str
    is_active: bool

    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    user: UserDb
    detail: str


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

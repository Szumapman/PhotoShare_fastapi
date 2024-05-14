import pickle
import uuid
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from jose import jwt, JWTError
from redis.asyncio import Redis


from src.conf.config import settings
from src.conf.constant import (
    AUTH,
    API,
    REDIS_EXPIRE,
    INVALID_SCOPE,
    COULD_NOT_VALIDATE_CREDENTIALS,
    ACCESS_TOKEN,
    REFRESH_TOKEN,
)
from src.database.models import User
from src.repository.abstract import AbstractUser
from src.database.dependencies import get_user_repository


class Auth:
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = settings.ALGORITHM
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API}{AUTH}/login")
    r = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=0,
    )

    def __init__(self, user_repository: AbstractUser):
        self.user_repository = user_repository

    async def create_access_token(
        self, data: dict, expires_delta: timedelta = timedelta(minutes=15)
    ) -> (str, str):
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        session_id = str(uuid.uuid4())
        to_encode.update(
            {
                "iat": datetime.utcnow(),
                "exp": expire,
                "session_id": session_id,
                "scope": ACCESS_TOKEN,
            }
        )
        encode_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encode_access_token, session_id

    async def create_refresh_token(
        self, data: dict, expires_delta: timedelta = timedelta(days=7)
    ) -> (str, datetime):
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": REFRESH_TOKEN}
        )
        encode_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encode_refresh_token, expire

    async def decode_refresh_token(self, refresh_token: str) -> str:
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == REFRESH_TOKEN:
                email = payload["sub"]
                return email
            return INVALID_SCOPE
        except JWTError:
            return COULD_NOT_VALIDATE_CREDENTIALS

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == ACCESS_TOKEN:
                email: str = payload["sub"]
                if email is None:
                    return COULD_NOT_VALIDATE_CREDENTIALS
            else:
                return COULD_NOT_VALIDATE_CREDENTIALS
        except JWTError:
            return COULD_NOT_VALIDATE_CREDENTIALS
        user = await self.r.get(f"user:{email}")
        if user is None:
            user = await self.user_repository.get_user_by_email(email)
            if user is None:
                return COULD_NOT_VALIDATE_CREDENTIALS
            await self.r.set(f"user:{email}", pickle.dumps(user))
            await self.r.expire(f"user:{email}", REDIS_EXPIRE)
        else:
            user = pickle.loads(user)
        return user


auth_service = Auth(get_user_repository())

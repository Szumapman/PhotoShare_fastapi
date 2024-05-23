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
    LOG_IN_AGAIN,
    ACCESS_TOKEN,
    REFRESH_TOKEN,
    ACCESS_TOKEN_EXPIRE,
    REFRESH_TOKEN_EXPIRE,
    BANNED_USER,
)
from src.database.models import User
from src.repository.abstract import AbstractUserRepo
from src.database.dependencies import get_user_repository


class Auth:
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API}{AUTH}/login")
    r = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        db=0,
    )

    async def update_user_in_redis(self, email: str, user: User):
        await self.r.set(f"user:{email}", pickle.dumps(user))
        await self.r.expire(f"user:{email}", REDIS_EXPIRE)

    async def create_access_token(
        self,
        data: dict,
        expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE),
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
        self,
        data: dict,
        expires_delta: timedelta = timedelta(days=REFRESH_TOKEN_EXPIRE),
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

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        user_repo: AbstractUserRepo = Depends(get_user_repository),
    ) -> User | str:
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
            user = await user_repo.get_user_by_email(email)
            if user is None:
                return COULD_NOT_VALIDATE_CREDENTIALS + f", email: {email}"
            await self.update_user_in_redis(email, user)
        else:
            user = pickle.loads(user)
        if await user_repo.is_user_logout(token):
            return LOG_IN_AGAIN
        if not user.is_active:
            return BANNED_USER
        return user

    async def get_session_id_from_token(self, token: str, user_email: str) -> str:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == ACCESS_TOKEN:
                email: str = payload["sub"]
                session_id = payload["session_id"]
                if email is None or email != user_email or session_id is None:
                    return COULD_NOT_VALIDATE_CREDENTIALS
                return session_id
            return COULD_NOT_VALIDATE_CREDENTIALS
        except JWTError:
            return COULD_NOT_VALIDATE_CREDENTIALS

    async def delete_user_from_redis(self, email: str):
        await self.r.delete(f"user:{email}")


auth_service = Auth()

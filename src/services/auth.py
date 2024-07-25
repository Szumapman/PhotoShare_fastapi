import pickle
import uuid
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from jose import jwt, JWTError
from redis.asyncio import Redis


from src.conf.config import settings
from src.conf.errors import UnauthorizedError, ForbiddenError
from src.conf.constants import (
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
    """
    This class is used to authenticate users. It uses OAuth2PasswordBearer and JWT to authenticate users.

    :param secret_key: secret key used to sign JWT
    :type secret_key: str
    :param algorithm: algorithm used to encrypt JWT
    :type algorithm: str
    :param oauth2_scheme: OAuth2PasswordBearer scheme
    :type oauth2_scheme: OAuth2PasswordBearer
    :param r: Redis client
    :type r: Redis
    """

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
        """
        This method is used to update user in Redis.

        :param email: email of user to update
        :type email: str
        :param user: user to update
        :type user: User
        :return: None
        """
        await self.r.set(f"user:{email}", pickle.dumps(user))
        await self.r.expire(f"user:{email}", REDIS_EXPIRE)

    async def create_access_token(
        self,
        data: dict,
        expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE),
    ) -> (str, str):
        """
        This method is used to create access token.

        :param data: data to encode
        :type data: dict
        :param expires_delta: delta to expire token
        :type expires_delta: timedelta
        :return: encoded access token and session id
        :rtype: (str, str)
        """
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
        """
        This method is used to create refresh token.

        :param data: data to encode
        :type data: dict
        :param expires_delta: delta to expire token
        :type expires_delta: timedelta
        :return: encoded refresh token and expire date
        :rtype: (str, datetime)
        """
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
        """
        This method is used to decode refresh token.

        :param refresh_token: refresh token to decode
        :type refresh_token: str
        :return: email decoded from refresh token
        :rtype: str
        :raise: UnauthorizedError if token has invalid scope or if token is invalid
        """
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == REFRESH_TOKEN:
                email = payload["sub"]
                return email
            raise UnauthorizedError(detail=INVALID_SCOPE)
        except JWTError:
            raise UnauthorizedError(detail=COULD_NOT_VALIDATE_CREDENTIALS)

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        user_repo: AbstractUserRepo = Depends(get_user_repository),
    ) -> User:
        """
        This method is used to get current authenticated user.
        :param token: token to decode
        :type token: str
        :param user_repo: repository to get user from
        :type user_repo: AbstractUserRepo
        :return: user decoded from token
        :rtype: User
        :raises:
            UnauthorizedError if token is invalid or user is logged out
            ForbiddenError if user is banned
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == ACCESS_TOKEN:
                email: str = payload["sub"]
                if email is None:
                    raise UnauthorizedError(detail=COULD_NOT_VALIDATE_CREDENTIALS)
            else:
                raise UnauthorizedError(detail=COULD_NOT_VALIDATE_CREDENTIALS)
        except JWTError:
            raise UnauthorizedError(detail=COULD_NOT_VALIDATE_CREDENTIALS)
        user = await self.r.get(f"user:{email}")
        if user is None:
            user = await user_repo.get_user_by_email(email)
            if user is None:
                raise UnauthorizedError(
                    detail=f"{COULD_NOT_VALIDATE_CREDENTIALS}, email: {email}"
                )
            await self.update_user_in_redis(email, user)
        else:
            user = pickle.loads(user)
        if await user_repo.is_user_logout(token):
            raise UnauthorizedError(detail=LOG_IN_AGAIN)
        if not user.is_active:
            raise ForbiddenError(detail=BANNED_USER)
        return user

    async def get_session_id_from_token(self, token: str, user_email: str) -> str:
        """
        This method is used to get session id from token.

        :param token: token to decode
        :type token: str
        :param user_email: user email to check
        :type user_email: str
        :return: session id decoded from token
        :rtype: str
        :raise: UnauthorizedError if token has invalid scope or if token is invalid
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == ACCESS_TOKEN:
                email: str = payload["sub"]
                session_id = payload["session_id"]
                if email is None or email != user_email or session_id is None:
                    raise UnauthorizedError(detail=COULD_NOT_VALIDATE_CREDENTIALS)
                return session_id
            raise UnauthorizedError(detail=COULD_NOT_VALIDATE_CREDENTIALS)
        except JWTError:
            raise UnauthorizedError(detail=COULD_NOT_VALIDATE_CREDENTIALS)

    async def delete_user_from_redis(self, email: str):
        """
        This method is used to delete user from redis.

        :param email: user email to delete
        :type email: str
        :return: None
        """
        await self.r.delete(f"user:{email}")


auth_service = Auth()

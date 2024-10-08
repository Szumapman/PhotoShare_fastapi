"""
Authentication routes
"""

from fastapi import APIRouter, HTTPException, status, Security, Depends
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from src.repository.abstract import AbstractUserRepo
from src.database.dependencies import (
    get_user_repository,
    get_avatar_provider,
    get_password_handler,
)
from src.services.auth import auth_service
from src.services.abstract import AbstractPasswordHandler
from src.services.avatar import AbstractAvatarProvider
from src.conf.constants import (
    AUTH,
    USER_LOGOUT,
    USER_CREATED,
    BANNED_USER,
    INCORRECT_USERNAME_OR_PASSWORD,
    USER_NOT_FOUND,
    RATE_LIMITER_INFO,
    RATE_LIMITER,
)
from src.schemas.users import UserInfo, UserIn, UserDb, TokenModel
from src.database.models import User
from src.conf.errors import NotFoundError, ConflictError

router = APIRouter(prefix=AUTH, tags=["auth"])
security = HTTPBearer()


async def __set_tokens(user: User, user_repo: AbstractUserRepo) -> TokenModel:
    """
    This helping function is used to create access and refresh tokens for a user.

    :param user: user to create tokens for
    :type user: User
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :return: tokens
    :rtype: TokenModel
    """
    access_token, session_id = await auth_service.create_access_token(
        data={"sub": user.email}
    )
    refresh_token, expiration_date = await auth_service.create_refresh_token(
        data={"sub": user.email, "session_id": session_id}
    )
    await user_repo.add_refresh_token(
        user.id, refresh_token, expiration_date, session_id
    )
    return TokenModel(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/signup",
    description=f"This endpoint is used to create a new user account. {RATE_LIMITER_INFO}",
    dependencies=[Depends(RATE_LIMITER)],
    response_model=UserInfo,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    user: UserIn,
    user_repo: AbstractUserRepo = Depends(get_user_repository),
    password_handler: AbstractPasswordHandler = Depends(get_password_handler),
    avatar_provider: AbstractAvatarProvider = Depends(get_avatar_provider),
):
    """
    This endpoint is used to create a new user account.

    :param user: new user data
    :type user: UserIn
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :param password_handler: password handler to work with
    :type password_handler: AbstractPasswordHandler
    :param avatar_provider: avatar provider to work with
    :type avatar_provider: AbstractAvatarProvider
    :return: info about the created user
    :rtype: UserInfo
    :raise: ConflictError: if account with this email or username already exists
    """
    if await user_repo.get_user_by_email(user.email):
        raise ConflictError(
            detail="Account with this email already exists",
        )
    if await user_repo.get_user_by_username(user.username):
        raise ConflictError(
            detail="Account with this username already exists",
        )
    user.password = password_handler.get_password_hash(user.password)
    avatar = avatar_provider.get_avatar(user.email, 255)
    user = await user_repo.create_user(user, avatar)
    return UserInfo(user=UserDb.model_validate(user), detail=USER_CREATED)


@router.post(
    "/login",
    description=f"This endpoint is used to login a user. {RATE_LIMITER_INFO}",
    dependencies=[
        Depends(
            RATE_LIMITER,
        )
    ],
    response_model=TokenModel,
)
async def login(
    body: OAuth2PasswordRequestForm = Depends(),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
    password_handler: AbstractPasswordHandler = Depends(get_password_handler),
):
    """
    This endpoint is used to login a user.

    :param body: password and username from request body
    :type body: OAuth2PasswordRequestForm
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :param password_handler: password handler to work with
    :type password_handler: AbstractPasswordHandler
    :return: tokens for user
    :rtype: TokenModel
    :raises:
        HTTPException(status_code=401, detail="Incorrect username or password") if username or password is incorrect
        HTTPException(status_code=403, detail="User is banned") if user is banned
    """
    user = await user_repo.get_user_by_email(body.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INCORRECT_USERNAME_OR_PASSWORD,
        )
    if not password_handler.verify_password(body.password, user.password):
        # incorrect password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INCORRECT_USERNAME_OR_PASSWORD,
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=BANNED_USER,
        )
    return await __set_tokens(user, user_repo)


@router.post(
    "/logout",
    description="This endpoint is used to logout current user from current session.",
    response_model=UserInfo,
)
async def logout(
    current_user: User = Depends(auth_service.get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    """
    This endpoint is used to logout current user from current session.

    :param current_user: user to logout
    :type current_user: User
    :param credentials: credentials for current user
    :type credentials: HTTPAuthorizationCredentials
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :return: info about the logout user
    :rtype: UserInfo
    """
    token = credentials.credentials
    session_id = await auth_service.get_session_id_from_token(token, current_user.email)
    user = await user_repo.logout_user(token, session_id, current_user)
    await auth_service.delete_user_from_redis(user.email)
    return UserInfo(user=UserDb.model_validate(user), detail=USER_LOGOUT)


@router.get(
    "/refresh_token",
    description=f"This endpoint is used to refresh tokens, using the refresh token. {RATE_LIMITER_INFO}",
    dependencies=[Depends(RATE_LIMITER)],
    response_model=TokenModel,
)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    """
    This endpoint is used to refresh tokens using the refresh token.

    :param credentials: current user credentials
    :type credentials: HTTPAuthorizationCredentials
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :return: tokens for user
    :rtype: TokenModel
    """
    old_refresh_token = credentials.credentials
    email = await auth_service.decode_refresh_token(old_refresh_token)
    user = await user_repo.get_user_by_email(email)
    if not user:
        raise NotFoundError(detail=USER_NOT_FOUND)
    await user_repo.delete_refresh_token(old_refresh_token, user.id)
    return await __set_tokens(user, user_repo)

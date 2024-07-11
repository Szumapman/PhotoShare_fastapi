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
from src.conf.constant import (
    AUTH,
    HTTP_401_UNAUTHORIZED_DETAILS,
    HTTP_404_NOT_FOUND_DETAILS,
    HTTP_403_FORBIDDEN_DETAILS,
    USER_LOGOUT,
    USER_CREATED,
    BANNED_USER,
    INCORRECT_USERNAME_OR_PASSWORD,
    USER_NOT_FOUND,
)
from src.schemas.users import UserInfo, UserIn, UserDb, TokenModel
from src.database.models import User
from src.conf.errors import UnauthorizedError, NotFoundError, ForbiddenError

router = APIRouter(prefix=AUTH, tags=["auth"])
security = HTTPBearer()


async def __set_tokens(user: User, user_repo: AbstractUserRepo) -> TokenModel:
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


@router.post("/signup", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
async def signup(
    user: UserIn,
    user_repo: AbstractUserRepo = Depends(get_user_repository),
    password_handler: AbstractPasswordHandler = Depends(get_password_handler),
    avatar_provider: AbstractAvatarProvider = Depends(get_avatar_provider),
):
    if await user_repo.get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account with this email already exists",
        )
    if await user_repo.get_user_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account with this username already exists",
        )
    user.password = password_handler.get_password_hash(user.password)
    avatar = avatar_provider.get_avatar(user.email, 255)
    user = await user_repo.create_user(user, avatar)
    return UserInfo(user=UserDb.model_validate(user), detail=USER_CREATED)


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
    password_handler: AbstractPasswordHandler = Depends(get_password_handler),
):
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


@router.post("/logout", response_model=UserInfo)
async def logout(
    current_user: User = Depends(auth_service.get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    try:
        token = credentials.credentials
        session_id = await auth_service.get_session_id_from_token(
            token, current_user.email
        )
        user = await user_repo.logout_user(token, session_id, current_user)
        await auth_service.delete_user_from_redis(user.email)
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    return UserInfo(user=UserDb.from_orm(user), detail=USER_LOGOUT)


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    try:
        old_refresh_token = credentials.credentials
        email = await auth_service.decode_refresh_token(old_refresh_token)
        user = await user_repo.get_user_by_email(email)
        if not user:
            raise NotFoundError(detail=USER_NOT_FOUND)
        await user_repo.delete_refresh_token(old_refresh_token, user.id)
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
    return await __set_tokens(user, user_repo)

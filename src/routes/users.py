from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File

from src.services.auth import auth_service
from src.database.dependencies import (
    get_user_repository,
    get_password_handler,
    get_photo_storage_provider,
)
from src.conf.constant import (
    USERS,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    FORBIDDEN_FOR_USER,
    FORBIDDEN_FOR_USER_AND_MODERATOR,
    USERNAME_EXISTS,
    EMAIL_EXISTS,
    USER_UPDATE,
    USER_DELETE,
    DEFAULT_AVATAR_URL_START_V1_GRAVATAR,
)
from src.schemas.users import (
    UserDb,
    UserIn,
    ActiveStatus,
    UserInfo,
    UserRoleIn,
    UserPublic,
    UserModeratorView,
)
from src.database.models import User
from src.repository.abstract import AbstractUserRepo
from src.services.abstract import AbstractPasswordHandler, AbstractPhotoStorageProvider

from src.conf.errors import NotFoundError, ForbiddenError, UnauthorizedError

router = APIRouter(prefix=USERS, tags=["users"])


@router.get(
    "/", response_model=list[UserDb] | list[UserModeratorView] | list[UserPublic]
)
async def get_users(
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    users = await user_repo.get_users()
    if current_user.role == ROLE_ADMIN:
        return [UserDb.model_validate(user) for user in users]
    elif current_user.role == ROLE_MODERATOR:
        return [UserModeratorView.model_validate(user) for user in users]
    return [UserPublic.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserDb | UserModeratorView | UserPublic)
async def get_user(
    user_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    user = await user_repo.get_user_by_id(user_id)
    if current_user.role == ROLE_ADMIN or current_user.id == user_id:
        return UserDb.model_validate(user)
    elif current_user.role == ROLE_MODERATOR:
        return UserModeratorView.model_validate(user)
    return UserPublic.model_validate(user)


@router.patch("/", response_model=UserInfo)
async def update_user(
    new_user_data: UserIn,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
    password_handler: AbstractPasswordHandler = Depends(get_password_handler),
):
    if new_user_data.username != current_user.username:
        if await user_repo.get_user_by_username(new_user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=USERNAME_EXISTS
            )
    if new_user_data.email != current_user.email:
        if await user_repo.get_user_by_email(new_user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=EMAIL_EXISTS
            )
    new_user_data.password = password_handler.get_password_hash(new_user_data.password)
    user = await user_repo.update_user(new_user_data, current_user.id)
    await auth_service.update_user_in_redis(user.email, user)
    return UserInfo(user=UserDb.model_validate(user), detail=USER_UPDATE)


@router.patch("/avatar", response_model=UserInfo)
async def update_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
    photo_storage_provider: AbstractPhotoStorageProvider = Depends(
        get_photo_storage_provider
    ),
):
    new_avatar_url = await photo_storage_provider.upload_avatar(file)
    if not current_user.avatar.startswith(DEFAULT_AVATAR_URL_START_V1_GRAVATAR):
        await photo_storage_provider.delete_avatar(current_user.avatar)
    user = await user_repo.update_user_avatar(current_user.id, new_avatar_url)
    await auth_service.update_user_in_redis(user.email, user)
    return UserInfo(user=UserDb.model_validate(user), detail=USER_UPDATE)


@router.delete("/{user_id}", response_model=UserInfo)
async def delete_user(
    user_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    if current_user.role == ROLE_ADMIN or current_user.id == user_id:
        user = await user_repo.get_user_by_id(user_id)
        user = await user_repo.delete_user(user.id)
        await auth_service.delete_user_from_redis(user.email)
        return UserInfo(user=UserDb.model_validate(user), detail=USER_DELETE)
    else:
        raise ForbiddenError(detail=FORBIDDEN_FOR_USER_AND_MODERATOR)


@router.patch("/{user_id}/active_status", response_model=UserInfo)
async def set_active_status(
    user_id: int,
    active_status: ActiveStatus,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    if current_user.role not in [ROLE_ADMIN, ROLE_MODERATOR]:
        raise ForbiddenError(detail=FORBIDDEN_FOR_USER)
    user = await user_repo.set_user_active_status(user_id, active_status, current_user)
    return UserInfo(
        user=UserDb.model_validate(user),
        detail=f"User status set to {'active' if active_status.is_active else 'banned'}.",
    )


@router.patch("/{user_id}/set_role", response_model=UserInfo)
async def set_role(
    user_id: int,
    role: UserRoleIn,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    if current_user.role != ROLE_ADMIN:
        raise ForbiddenError(detail=FORBIDDEN_FOR_USER_AND_MODERATOR)
    user = await user_repo.set_user_role(user_id, role)
    await auth_service.update_user_in_redis(user.email, user)
    return UserInfo(
        user=UserDb.model_validate(user), detail=f"User role set to {user.role}."
    )

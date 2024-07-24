from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Query

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
    RATE_LIMITER,
    RATE_LIMITER_INFO,
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

from src.conf.errors import ForbiddenError

router = APIRouter(prefix=USERS, tags=["users"])


@router.get(
    "/",
    description=f"This endpoint is used to get all users. "
    f"Depending on the user role, the endpoint will return different data views. {RATE_LIMITER_INFO}",
    dependencies=[Depends(RATE_LIMITER)],
    response_model=list[UserDb] | list[UserModeratorView] | list[UserPublic],
)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    """
    This endpoint is used to get all users with pagination.
    Depending on the user role, the endpoint will return different data views.

    :param skip: number of users to skip
    :type skip: int
    :param limit: number of users to return
    :type limit: int
    :param current_user: user who performed request
    :type current_user: User
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :return: users
    :rtype: list[UserDb] if current_user role is admin |
            list[UserModeratorView] if current_user role is moderator |
            list[UserPublic] if current_user role is standard
    """
    users = await user_repo.get_users(skip, limit)
    if current_user.role == ROLE_ADMIN:
        return [UserDb.model_validate(user) for user in users]
    elif current_user.role == ROLE_MODERATOR:
        return [UserModeratorView.model_validate(user) for user in users]
    return [UserPublic.model_validate(user) for user in users]


@router.get(
    "/{user_id}",
    description=f"This endpoint is used to get user by id. "
    f"Depending on the user role, the endpoint will return different data views. {RATE_LIMITER_INFO}",
    dependencies=[Depends(RATE_LIMITER)],
    response_model=UserDb | UserModeratorView | UserPublic,
)
async def get_user(
    user_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    """
    This endpoint is used to get user by id. Depending on the user role, the endpoint will return different data views.

    :param user_id: id of user to get
    :type user_id: int
    :param current_user: user who performed request
    :type current_user: User
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :return: user
    :rtype: UserDb if current_user role is admin |
            UserModeratorView if current_user role is moderator |
            UserPublic if current_user role is standard
    """
    user = await user_repo.get_user_by_id(user_id)
    if current_user.role == ROLE_ADMIN or current_user.id == user_id:
        return UserDb.model_validate(user)
    elif current_user.role == ROLE_MODERATOR:
        return UserModeratorView.model_validate(user)
    return UserPublic.model_validate(user)


@router.patch(
    "/", description=f"This endpoint is used to update user.", response_model=UserInfo
)
async def update_user(
    new_user_data: UserIn,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
    password_handler: AbstractPasswordHandler = Depends(get_password_handler),
):
    """
    This endpoint is used to update user.

    :param new_user_data: new user data
    :type new_user_data: UserIn
    :param current_user: user who performed request
    :type current_user: User
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :param password_handler: password handler to work with
    :type password_handler: AbstractPasswordHandler
    :return: updated user with confirmation message
    :rtype: UserInfo
    """
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


@router.patch(
    "/avatar",
    description=f"This endpoint is used to update user avatar. {RATE_LIMITER_INFO}",
    dependencies=[Depends(RATE_LIMITER)],
    response_model=UserInfo,
)
async def update_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
    photo_storage_provider: AbstractPhotoStorageProvider = Depends(
        get_photo_storage_provider
    ),
):
    """
    This endpoint is used to update user avatar.

    :param file: new avatar file
    :type file: UploadFile
    :param current_user: user who performed request
    :type current_user: User
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :param photo_storage_provider: photo storage provider to work with
    :type photo_storage_provider: AbstractPhotoStorageProvider
    :return: updated user with confirmation message
    :rtype: UserInfo
    """
    new_avatar_url = await photo_storage_provider.upload_avatar(file)
    if not current_user.avatar.startswith(DEFAULT_AVATAR_URL_START_V1_GRAVATAR):
        await photo_storage_provider.delete_avatar(current_user.avatar)
    user = await user_repo.update_user_avatar(current_user.id, new_avatar_url)
    await auth_service.update_user_in_redis(user.email, user)
    return UserInfo(user=UserDb.model_validate(user), detail=USER_UPDATE)


@router.delete(
    "/{user_id}",
    description=f"This endpoint is used to delete user.",
    response_model=UserInfo,
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    """
    This endpoint is used to delete user.

    :param user_id: id of user to delete
    :type user_id: int
    :param current_user: user who performed request
    :type current_user: User
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :return: deleted user with confirmation message
    :rtype: UserInfo
    :raise: ForbiddenError if current_user role is not admin or user_id is not equal to current_user id
    """
    if current_user.role == ROLE_ADMIN or current_user.id == user_id:
        user = await user_repo.get_user_by_id(user_id)
        user = await user_repo.delete_user(user.id)
        await auth_service.delete_user_from_redis(user.email)
        return UserInfo(user=UserDb.model_validate(user), detail=USER_DELETE)
    else:
        raise ForbiddenError(detail=FORBIDDEN_FOR_USER_AND_MODERATOR)


@router.patch(
    "/{user_id}/active_status",
    description=f"This endpoint is used to set user active status.",
    response_model=UserInfo,
)
async def set_active_status(
    user_id: int,
    active_status: ActiveStatus,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    """
    This endpoint is used to set user active status.

    :param user_id: id of user to set active status
    :type user_id: int
    :param active_status: new active status
    :type active_status: ActiveStatus
    :param current_user: user who performed request
    :type current_user: User
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :return: updated user with confirmation message
    :rtype: UserInfo
    :raise: ForbiddenError if current_user role is not admin or moderator
    """
    if current_user.role not in [ROLE_ADMIN, ROLE_MODERATOR]:
        raise ForbiddenError(detail=FORBIDDEN_FOR_USER)
    user = await user_repo.set_user_active_status(user_id, active_status, current_user)
    return UserInfo(
        user=UserDb.model_validate(user),
        detail=f"User status set to {'active' if active_status.is_active else 'banned'}.",
    )


@router.patch(
    "/{user_id}/set_role",
    description="This endpoint is used to set user role.",
    response_model=UserInfo,
)
async def set_role(
    user_id: int,
    role: UserRoleIn,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    """
    This endpoint is used to set user role.

    :param user_id: id of user to set role
    :type user_id: int
    :param role: new role
    :type role: UserRoleIn
    :param current_user: user who performed request
    :type current_user: User
    :param user_repo: repository to work with
    :type user_repo: AbstractUserRepo
    :return: updated user with confirmation message
    :rtype: UserInfo
    :raise: ForbiddenError if current_user role is not admin
    """
    if current_user.role != ROLE_ADMIN:
        raise ForbiddenError(detail=FORBIDDEN_FOR_USER_AND_MODERATOR)
    user = await user_repo.set_user_role(user_id, role)
    await auth_service.update_user_in_redis(user.email, user)
    return UserInfo(
        user=UserDb.model_validate(user), detail=f"User role set to {user.role}."
    )

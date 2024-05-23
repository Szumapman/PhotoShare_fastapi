from fastapi import APIRouter, HTTPException, Depends, status

from src.services.auth import auth_service
from src.database.dependencies import get_user_repository
from src.conf.constant import (
    USERS,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    HTTP_404_NOT_FOUND_DETAILS,
    HTTP_403_FORBIDDEN_DETAILS,
    FORBIDDEN_FOR_USER,
    FORBIDDEN_FOR_USER_AND_MODERATOR,
    USER_NOT_FOUND,
    USERNAME_EXISTS,
    EMAIL_EXISTS,
    USER_UPDATE,
    USER_DELETE,
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
from src.routes.auth import __is_current_user_logged_in
from src.services.pasword import get_password_hash

router = APIRouter(prefix=USERS, tags=["users"])


@router.get(
    "/", response_model=list[UserDb] | list[UserModeratorView] | list[UserPublic]
)
async def get_users(
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    if await __is_current_user_logged_in(current_user):
        users = await user_repo.get_users()
        if current_user.role == ROLE_ADMIN:
            return [UserDb.from_orm(user) for user in users]
        elif current_user.role == ROLE_MODERATOR:
            return [UserModeratorView.from_orm(user) for user in users]
        return [UserPublic.from_orm(user) for user in users]


@router.get("/{user_id}", response_model=UserDb | UserModeratorView | UserPublic)
async def get_user(
    user_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    if await __is_current_user_logged_in(current_user):
        user = await user_repo.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=USER_NOT_FOUND,
            )
        if current_user.role == ROLE_ADMIN or current_user.id == user_id:
            return UserDb.from_orm(user)
        elif current_user.role == ROLE_MODERATOR:
            return UserModeratorView.from_orm(user)
        return UserPublic.from_orm(user)


@router.patch("/", response_model=UserInfo)
async def update_user(
    new_user_data: UserIn,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    if await __is_current_user_logged_in(current_user):
        if new_user_data.username != current_user.username:
            print(new_user_data.username, current_user.username)
            if await user_repo.get_user_by_username(new_user_data.username):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail=USERNAME_EXISTS
                )
        elif new_user_data.email != current_user.email:
            if await user_repo.get_user_by_email(new_user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail=EMAIL_EXISTS
                )
        new_user_data.password = get_password_hash(new_user_data.password)
        user = await user_repo.update_user(new_user_data, current_user.id)
        await auth_service.update_user_in_redis(user.email, user)
        return UserInfo(user=UserDb.model_validate(user), detail=USER_UPDATE)


@router.delete("/{user_id}", response_model=UserInfo)
async def delete_user(
    user_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    if await __is_current_user_logged_in(current_user):
        if current_user.role == ROLE_ADMIN or current_user.id == user_id:
            user = await user_repo.delete_user(user_id)
            if user in HTTP_404_NOT_FOUND_DETAILS:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=user,
                )
            await auth_service.delete_user_from_redis(user.email)
            return UserInfo(user=UserDb.model_validate(user), detail=USER_DELETE)


@router.patch("/active_status/{user_id}", response_model=UserInfo)
async def set_active_status(
    user_id: int,
    active_status: ActiveStatus,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    if await __is_current_user_logged_in(current_user):
        if current_user.role not in [ROLE_ADMIN, ROLE_MODERATOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=FORBIDDEN_FOR_USER,
            )
        answer = await user_repo.set_user_active_status(
            user_id, active_status, current_user
        )
        if answer in HTTP_404_NOT_FOUND_DETAILS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=answer)
        elif answer in HTTP_403_FORBIDDEN_DETAILS:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=answer)
        user = answer
        return UserInfo(
            user=UserDb.from_orm(user),
            detail=f"User status set to {'active' if active_status.is_active else 'banned'}.",
        )


@router.patch("/set_role/{user_id}", response_model=UserInfo)
async def set_role(
    user_id: int,
    role: UserRoleIn,
    current_user: User = Depends(auth_service.get_current_user),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    if await __is_current_user_logged_in(current_user):
        if current_user.role != ROLE_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=FORBIDDEN_FOR_USER_AND_MODERATOR,
            )
        answer = await user_repo.set_user_role(user_id, role)
        if answer in HTTP_404_NOT_FOUND_DETAILS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=answer)
        user = answer
        return UserInfo(
            user=UserDb.from_orm(user), detail=f"User role set to {role.role.value}."
        )

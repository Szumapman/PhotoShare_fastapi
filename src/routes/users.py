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
)
from src.schemas.users import UserDb, ActiveStatus, UserInfo, UserRoleIn
from src.database.models import User
from src.repository.abstract import AbstractUserRepo
from src.routes.auth import __is_current_user_logged_in


router = APIRouter(prefix=USERS, tags=["users"])


@router.get("/me", response_model=UserDb)
async def get_current_user(
    current_user: User = Depends(auth_service.get_current_user),
) -> UserDb:
    if __is_current_user_logged_in(current_user):
        return UserDb.from_orm(current_user)


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

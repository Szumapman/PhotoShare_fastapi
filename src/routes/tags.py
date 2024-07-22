from fastapi import APIRouter, Depends, status, Query

from src.conf.errors import ForbiddenError, ConflictError
from src.database.dependencies import get_tag_repository
from src.schemas.tags import TagIn, TagInfo, TagOut
from src.schemas.users import UserDb
from src.services.auth import auth_service
from src.repository.abstract import AbstractTagRepo
from src.conf.constant import (
    TAGS,
    TAG_CREATED,
    TAG_ALREADY_EXISTS,
    TAG_UPDATED,
    TAG_DELETED,
    FORBIDDEN_FOR_USER,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    TAGS_GET_ENUM,
    FORBIDDEN_FOR_USER_AND_MODERATOR,
)

router = APIRouter(prefix=TAGS, tags=["tags"])


@router.post("/", response_model=TagInfo, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_in: TagIn,
    current_user: UserDb = Depends(auth_service.get_current_user),
    tag_repo: AbstractTagRepo = Depends(get_tag_repository),
):
    """
    Create a new tag.
    :param tag_in: tag name
    :type tag_in: TagIn
    :param current_user: user who created tag
    :type current_user: UserDb
    :param tag_repo: repository for tags
    :type tag_repo: AbstractTagRepo
    :return: confirmation of creation with tag info
    :rtype: TagInfo
    """
    if await tag_repo.get_tag_by_name(tag_in.name):
        raise ConflictError(detail=TAG_ALREADY_EXISTS)
    tag = await tag_repo.create_tag(tag_in.name)
    return TagInfo(tag=TagOut.model_validate(tag), detail=TAG_CREATED)


@router.get("/", response_model=list[TagOut])
async def get_tags(
    current_user: UserDb = Depends(auth_service.get_current_user),
    tag_repo: AbstractTagRepo = Depends(get_tag_repository),
    sort_by: str | None = Query(
        None,
        enum=TAGS_GET_ENUM,
        description="Sort alphabetically ascending or descending",
    ),
    skip: int = 0,
    limit: int = 10,
):
    """
    Get all tags.
    :param current_user: user who performed request
    :type current_user: UserDb
    :param tag_repo: repository for tags
    :type tag_repo: AbstractTagRepo
    :param sort_by: how to sort tags (optional)
    :type sort_by: str | None
    :param skip: number of tags to skip
    :type skip: int
    :param limit: number of tags to get
    :return: list of tags
    :rtype: list[TagOut]
    """
    tags = await tag_repo.get_tags(sort_by, skip, limit)
    return [TagOut.model_validate(tag) for tag in tags]


@router.get("/{tag_id}", response_model=TagOut)
async def get_tag_by_id(
    tag_id: int,
    current_user: UserDb = Depends(auth_service.get_current_user),
    tag_repo: AbstractTagRepo = Depends(get_tag_repository),
):
    """
    Get tag by id.
    :param tag_id: id of tag to get
    :type tag_id: int
    :param current_user: user who performed request
    :type current_user: UserDb
    :param tag_repo: repository for tags
    :type tag_repo: AbstractTagRepo
    :return: tag
    :rtype: TagOut
    """
    tag = await tag_repo.get_tag_by_id(tag_id)
    return TagOut.model_validate(tag)


@router.put("/{tag_id}", response_model=TagInfo)
async def update_tag(
    tag_id: int,
    tag_in: TagIn,
    current_user: UserDb = Depends(auth_service.get_current_user),
    tag_repo: AbstractTagRepo = Depends(get_tag_repository),
):
    """
    Update tag by id. Only admin or moderator can update tags.

    :param tag_id: id of tag to update
    :type tag_id: int
    :param tag_in: new tag name
    :type tag_in: TagIn
    :param current_user: user who performed request
    :type current_user: UserDb
    :param tag_repo: repository for tags
    :type tag_repo: AbstractTagRepo
    :return: updated tag
    :rtype: TagInfo
    """
    if current_user.role not in [ROLE_ADMIN, ROLE_MODERATOR]:
        raise ForbiddenError(detail=FORBIDDEN_FOR_USER)
    tag = await tag_repo.update_tag(tag_id, tag_in.name)
    return TagInfo(tag=TagOut.model_validate(tag), detail=TAG_UPDATED)


@router.delete("/{tag_id}", response_model=TagInfo)
async def delete_tag(
    tag_id: int,
    current_user: UserDb = Depends(auth_service.get_current_user),
    tag_repo: AbstractTagRepo = Depends(get_tag_repository),
):
    """
    Delete tag by id. Only admin can delete tags.

    :param tag_id: id of tag to delete
    :type tag_id: int
    :param current_user: user who performed request
    :type current_user: UserDb
    :param tag_repo: repository for tags
    :type tag_repo: AbstractTagRepo
    :return: confirmation of deletion with deleted tag
    :rtype: TagInfo
    """
    if current_user.role != ROLE_ADMIN:
        raise ForbiddenError(detail=FORBIDDEN_FOR_USER_AND_MODERATOR)
    tag = await tag_repo.delete_tag(tag_id)
    return TagInfo(tag=TagOut.model_validate(tag), detail=TAG_DELETED)

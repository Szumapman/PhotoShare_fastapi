from fastapi import APIRouter, Depends, status
from fastapi_limiter.depends import RateLimiter

from src.conf.errors import ForbiddenError
from src.database.dependencies import get_comment_repository, get_photo_repository
from src.services.auth import auth_service
from src.repository.abstract import AbstractCommentRepo, AbstractPhotoRepo
from src.conf.constants import (
    COMMENTS,
    COMMENT_CREATED,
    COMMENT_UPDATED,
    FORBIDDEN_FOR_USER,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    COMMENT_DELETED,
    RATE_LIMITER,
    RATE_LIMITER_INFO,
)
from src.schemas.comments import CommentInfo, CommentIn, CommentOut, CommentUpdate
from src.schemas.users import UserDb

router = APIRouter(prefix=COMMENTS, tags=["comments"])


@router.post(
    "/",
    description=f"This endpoint is used to create new comment. {RATE_LIMITER_INFO}",
    dependencies=[Depends(RATE_LIMITER)],
    status_code=status.HTTP_201_CREATED,
    response_model=CommentInfo,
)
async def create_comment(
    comment: CommentIn,
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
    comment_repo: AbstractCommentRepo = Depends(get_comment_repository),
):
    """
    Create a new comment.

    :param comment: comment data including content and photo_id
    :type comment: CommentIn
    :param current_user: user who created comment
    :type current_user: UserDb
    :param photo_repo: repository for photos
    :type photo_repo: AbstractPhotoRepo
    :param comment_repo: repository for comments
    :type comment_repo: AbstractCommentRepo
    :return: new comment with confirmation of creation
    :rtype: CommentInfo
    """
    await photo_repo.get_photo_by_id(comment.photo_id)  # to check if photo exists
    comment = await comment_repo.create_comment(
        comment.content, comment.photo_id, current_user.id
    )
    return CommentInfo(
        comment=CommentOut.model_validate(comment), detail=COMMENT_CREATED
    )


@router.get(
    "/",
    description="This endpoint is used to get all comments for a specific photo.",
    response_model=list[CommentOut],
)
async def get_comments(
    photo_id: int,
    current_user: UserDb = Depends(auth_service.get_current_user),
    comment_repo: AbstractCommentRepo = Depends(get_comment_repository),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
):
    """
    Get all comments for a photo.

    :param photo_id: id of photo to get comments for
    :type photo_id: int
    :param current_user: user who performed request
    :type current_user: UserDb
    :param comment_repo: repository for comments
    :type comment_repo: AbstractCommentRepo
    :param photo_repo: repository for photos
    :type photo_repo: AbstractPhotoRepo
    :return: list of comments
    :rtype: list[CommentOut]
    """
    await photo_repo.get_photo_by_id(photo_id)  # to check if photo exists
    comments = await comment_repo.get_comments(photo_id)
    return [CommentOut.model_validate(comment) for comment in comments]


@router.get(
    "/{comment_id}",
    description="This endpoint is used to get a comment by id.",
    response_model=CommentOut,
)
async def get_comment(
    comment_id: int,
    current_user: UserDb = Depends(auth_service.get_current_user),
    comment_repo: AbstractCommentRepo = Depends(get_comment_repository),
):
    """
    Get a comment by id.

    :param comment_id: id of comment to get
    :type comment_id: int
    :param current_user: user who performed request
    :type current_user: UserDb
    :param comment_repo: repository for comments
    :type comment_repo: AbstractCommentRepo
    :return: comment
    :rtype: CommentOut
    """
    comment = await comment_repo.get_comment_by_id(comment_id)
    return CommentOut.model_validate(comment)


@router.patch(
    "/{comment_id}",
    description="This endpoint is used to update a comment.",
    response_model=CommentInfo,
)
async def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    current_user: UserDb = Depends(auth_service.get_current_user),
    comment_repo: AbstractCommentRepo = Depends(get_comment_repository),
):
    """
    Update a comment.

    :param comment_id: id of comment to update
    :type comment_id: int
    :param comment: new comment data including content
    :type comment: CommentUpdate
    :param current_user: user who performed request
    :type current_user: UserDb
    :param comment_repo: repository for comments
    :type comment_repo: AbstractCommentRepo
    :return: updated comment with confirmation of update
    :rtype: CommentInfo
    """
    comment = await comment_repo.update_comment(
        comment_id, current_user.id, comment.content
    )
    return CommentInfo(
        comment=CommentOut.model_validate(comment), detail=COMMENT_UPDATED
    )


@router.delete(
    "/{comment_id}",
    description="This endpoint is used to delete a comment.",
    response_model=CommentInfo,
)
async def delete_comment(
    comment_id: int,
    current_user: UserDb = Depends(auth_service.get_current_user),
    comment_repo: AbstractCommentRepo = Depends(get_comment_repository),
):
    """
    Delete a comment - allow only for admin and moderator.

    :param comment_id: id of comment to delete
    :type comment_id: int
    :param current_user: user who performed request
    :type current_user: UserDb
    :param comment_repo: repository for comments
    :type comment_repo: AbstractCommentRepo
    :return: deleted comment with confirmation of deletion
    :rtype: CommentInfo
    """
    if current_user.role not in [ROLE_ADMIN, ROLE_MODERATOR]:
        raise ForbiddenError(detail=FORBIDDEN_FOR_USER)
    comment = await comment_repo.delete_comment(comment_id)
    return CommentInfo(
        comment=CommentOut.model_validate(comment), detail=COMMENT_DELETED
    )

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from src.conf.constant import MAX_COMMENT_LENGTH


class CommentUpdate(BaseModel):
    """
    Comment model for updating comment.

    :param content: content of comment
    :type content: str
    """

    content: str = Field(default="", max_length=MAX_COMMENT_LENGTH)


class CommentIn(CommentUpdate):
    """
    Comment model for creating / updating comment.

    :param photo_id: id of photo that comment belongs to
    :type photo_id: int
    """

    photo_id: int


class CommentOut(CommentIn):
    """
    Comment model for returning comment from database.

    :param id: id of comment
    :type id: int
    :param user_id: id of user that created comment
    :type user_id: int
    :param created_at: date and time when comment was created
    :type created_at: datetime
    :param updated_at: date and time when comment was updated
    :type updated_at: datetime | None
    """

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CommentInfo(BaseModel):
    """
    Model for returning info about performed operation and comment.

    Attributes:
        comment (CommentOut): Comment model for returning comment from database.
        detail (str): Detail of performed operation.
    """

    comment: CommentOut
    detail: str

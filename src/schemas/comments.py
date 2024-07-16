from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.conf.constant import MAX_COMMENT_LENGTH


class CommentIn(BaseModel):
    """
    Comment model for creating / updating comment.

    :param text: text of comment
    :type text: str
    """

    text: str = Field()

    @field_validator("text")
    def text_validator(cls, text: str) -> str:
        """
        Validate comment text.
        :param text: text of comment
        :return: comment text
        :raise: ValueError if comment text is too long
        """
        if len(text) > MAX_COMMENT_LENGTH:
            raise ValueError(
                f"The comment is too long. The maximum length of a comment is: {MAX_COMMENT_LENGTH} signs"
            )
        return text


class CommentOut(CommentIn):
    """
    Comment model for returning comment from database.

    :param id: id of comment
    :type id: int
    :param photo_id: id of photo that comment belongs to
    :type photo_id: int
    :param user_id: id of user that created comment
    :type user_id: int
    :param created_at: date and time when comment was created
    :type created_at: datetime
    :param updated_at: date and time when comment was updated
    :type updated_at: datetime | None
    """

    id: int
    photo_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

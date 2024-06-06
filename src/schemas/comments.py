from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.conf.constant import MAX_COMMENT_LENGTH


class CommentIn(BaseModel):
    text: str = Field()

    @field_validator("text")
    def text_validator(cls, text: str) -> str:
        if len(text) > MAX_COMMENT_LENGTH:
            raise ValueError(
                f"The comment is too long. The maximum length of a comment is: {MAX_COMMENT_LENGTH} signs"
            )
        return text


class CommentOut(CommentIn):
    id: int
    photo_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

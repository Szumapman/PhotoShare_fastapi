from datetime import datetime
import json

from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict

from src.conf.constant import (
    MAX_DESCRIPTION_LENGTH,
    MAX_TAGS_AMOUNT,
)
from src.schemas.tags import TagIn, TagOut
from src.schemas.comments import CommentOut


class PhotoIn(BaseModel):
    description: str = Field()
    tags: list[TagIn] | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value

    @field_validator("description")
    def validate_description(cls, description: str) -> str:
        if len(description.strip()) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description too long. Max description length is {MAX_DESCRIPTION_LENGTH}."
            )
        if len(description.strip()) == 0:
            raise ValueError("Description cannot be empty.")
        return description

    @field_validator("tags")
    def validate_tags(cls, tags: list[TagIn]) -> list[TagIn] | None:
        if tags and len(tags) > MAX_TAGS_AMOUNT:
            raise ValueError(
                f"Too many tags. You can't add more than {MAX_TAGS_AMOUNT} tags."
            )
        return tags


class PhotoCreated(PhotoIn):
    id: int
    photo_url: str
    qr_url: str
    uploaded_at: datetime


class PhotoOut(PhotoIn):
    id: int
    user_id: int
    photo_url: str
    qr_url: str
    transformation: dict[str, list] | None = None
    uploaded_at: datetime
    tags: list[TagOut] | None = None
    comments: list[CommentOut] | None = None
    rating: float | None = None

    model_config = {"from_attributes": True}

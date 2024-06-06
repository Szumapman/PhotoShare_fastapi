import re

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.conf.constant import MAX_TAG_NAME_LENGTH


class TagIn(BaseModel):
    name: str = Field()

    @field_validator("name")
    def validate_tag_name(cls, name: str) -> str:
        if len(name) > MAX_TAG_NAME_LENGTH:
            raise ValueError(
                f"Tag name must be less than {MAX_TAG_NAME_LENGTH} characters"
            )
        regex = re.compile(r"[_!#$%^&*()<>?/|}{~:]")
        if regex.search(name):
            raise ValueError(f"Tag name contains invalid characters")
        return name


class TagOut(TagIn):
    id: int

    model_config = ConfigDict(from_attributes=True)

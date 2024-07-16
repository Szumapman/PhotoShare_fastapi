import re

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.conf.constant import MAX_TAG_NAME_LENGTH


class TagIn(BaseModel):
    """
    Tag model for creating / updating tag.

    :param name: name of tag
    :type name: str
    """

    name: str = Field()

    @field_validator("name")
    def validate_tag_name(cls, name: str) -> str:
        """
        Validate tag name.

        :param name: name of tag
        :return: name of tag
        :raise: ValueError if tag name is too long or contains invalid characters
        """
        if len(name) > MAX_TAG_NAME_LENGTH:
            raise ValueError(
                f"Tag name must be less than {MAX_TAG_NAME_LENGTH} characters"
            )
        regex = re.compile(r"[*^()<>?/|}{~:]")
        if regex.search(name):
            raise ValueError(f"Tag name contains invalid characters")
        return name


class TagOut(TagIn):
    """
    Tag model for returning tag from database. Inherits from TagIn.

    :param id: id of tag
    :type id: int
    """

    id: int

    model_config = ConfigDict(from_attributes=True)

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
    """
    Photo model for creating / updating photo data.

    :param description: description of photo
    :type description: str
    :param tags: tags of photo
    :type tags: list[TagIn] | None
    """

    description: str = Field()
    tags: list[TagIn] | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        """
        Convert model to json if it is a string.

        :param value: json or model
        :return: json model
        """
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value

    @field_validator("description")
    def validate_description(cls, description: str) -> str:
        """
        Validate description.
        :param description: description of photo
        :return: description of photo
        :raise: ValueError if description is too long or empty
        """
        if len(description.strip()) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description too long. Max description length is {MAX_DESCRIPTION_LENGTH}."
            )
        if len(description.strip()) == 0:
            raise ValueError("Description cannot be empty.")
        return description

    @field_validator("tags")
    def validate_tags(cls, tags: list[TagIn]) -> list[TagIn] | None:
        """
        Validate tags.
        :param tags: tags of photo
        :return: tags of photo
        :raise: ValueError if too many tags are given
        """
        if tags and len(tags) > MAX_TAGS_AMOUNT:
            raise ValueError(
                f"Too many tags. You can't add more than {MAX_TAGS_AMOUNT} tags."
            )
        return tags


class PhotoOut(PhotoIn):
    """
    Photo model for returning photo from database.

    :param id: id of photo
    :type id: int
    :param user_id: id of user who uploaded photo
    :type user_id: int
    :param photo_url: url of photo
    :type photo_url: str
    :param uploaded_at: date and time when photo was uploaded
    :type uploaded_at: datetime
    :param tags: tags of photo
    :type tags: list[TagOut] | None
    :param comments: comments of photo
    :type comments: list[CommentOut] | None
    :param rating: rating of photo
    :type rating: float | None
    """

    id: int
    user_id: int
    photo_url: str
    transformations: dict[str, list] | None = None
    uploaded_at: datetime
    tags: list[TagOut] | None = None
    comments: list[CommentOut] | None = None
    rating: float | None = None

    model_config = ConfigDict(from_attributes=True)


class PhotoInfo(BaseModel):
    """
    Model for returning info about performed operation and photo.

    Attributes:
        photo (PhotoOut): Photo model for returning photo from database.
        detail (str): Detail of performed operation.
    """

    photo: PhotoOut
    detail: str


class TransformIn(BaseModel):
    """
    Data model for transformation parameters given by user.

    Attributes:
        background (str): The background color of the transformation (e.g. blue, red).
        aspect_ratio (str): The aspect ratio of the transformation (e.g. 16:10)
        gravity (str): The gravity of the transformation (e.g. south, west or face).
        angle (int): The angle of the transformation (e.g. -30 or 20, 0 means do not change).
        width (int): The width of the transformed image (must be greater than 0, 0 means do not change).
        height (int): The height of the transformed image (must be greater than 0, 0 means do not change).
        crop (str): The crop effects like:
            fill, lfill, fill_pad, crop, thumb, auto, scale, fit, limit, mfit, pad, lpad, mpad, imagga_scale, imagga_crop
        effects (list[str]): The cloudinary transformation effects like:
            art:al_dente/athena/audrey/aurora/daguerre/eucalyptus/fes/frost/hairspray/hokusai/incognito/linen/peacock
                /primavera/quartz/red_rock/refresh/sizzle/sonnet/ukulele/zorro,
            cartoonify, pixelate, saturation, blur, sepia, grayscale, vignette - you can add :value (e.g. 20)

        more info:
            cloudinary docs: https://cloudinary.com/documentation/transformation_reference
    """

    background: str = ""
    aspect_ratio: str = ""
    gravity: str = ""
    angle: int = 0
    width: int = 0
    height: int = 0
    crop: str = ""
    effects: list[str] = []

    @field_validator("width", "height")
    def validate_width_height(cls, value) -> int:
        """
        Validate width and height of transformation parameters.

        :param value: width or height of transformation parameters
        :return: width or height of transformation parameters
        :raise: ValueError if value is negative
        """
        if value < 0:
            raise ValueError("The value cannot be negative.")
        return value

    @field_validator("effects")
    def validate_effects(cls, effects) -> list[str]:
        """
        Validate effects of transformation parameters.

        :param effects: effects given by user
        :return: effects
        """
        if effects and len(effects) > 0:
            for effect in effects:
                effect, *_ = effect.split(":")
                if effect not in [
                    "art",
                    "cartoonify",
                    "pixelate",
                    "saturation",
                    "blur",
                    "sepia",
                    "grayscale",
                    "vignette",
                ]:
                    raise ValueError(
                        "The value of the effect has to be one of the following: art, cartoonify, pixelate,"
                        "saturation, blur, sepia, grayscale, vignette"
                    )
        return effects


class RatingIn(BaseModel):
    """
    Data model for rating given by user.

    Attributes:
        score (int): The rating score from 1 to 5
    """

    score: int = Field(..., ge=1, le=5, description="The rating score from 1 to 5")


class RatingOut(RatingIn):
    """
    Data model for rating returned from database. Inherits from RatingIn

    Attributes:
        photo_id (int): The id of the rated photo
        user_id (int): The id of the user who rated the photo
    """

    photo_id: int
    user_id: int

    model_config = {"from_attributes": True}


class RatingInfo(BaseModel):
    """
    Model for returning info about performed operation and rating.

    Attributes:
        rating (RatingOut): The rating object
        detail (str): The detail of performed operation
    """

    rating: RatingOut
    detail: str

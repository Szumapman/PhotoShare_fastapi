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
    transformations: dict[str, list] | None = None
    uploaded_at: datetime
    tags: list[TagOut] | None = None
    comments: list[CommentOut] | None = None
    rating: float | None = None

    model_config = {"from_attributes": True}


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
        if value < 0:
            raise ValueError("The value cannot be negative.")
        return value

    @field_validator("effects")
    def validate_effects(cls, effects) -> list[str]:
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

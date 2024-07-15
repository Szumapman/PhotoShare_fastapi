from io import BytesIO

import cloudinary
import cloudinary.uploader
from fastapi import File

from src.services.abstract import AbstractPhotoStorageProvider
from src.schemas.photos import PhotoOut, TransformIn
from src.conf.config import settings
from src.conf.constant import (
    CLOUDINARY_PHOTO_PUBLIC_ID_PREFIX,
    CLOUDINARY_AVATAR_PUBLIC_ID_PREFIX,
    AVATAR_WIDTH,
    AVATAR_HEIGHT,
)
from src.conf.logger import logger
from src.conf.errors import PhotoStorageProviderError, NotFoundError


class CloudinaryPhotoStorageProvider(AbstractPhotoStorageProvider):
    def __init__(self):
        self.config = cloudinary.config(
            cloud_name=settings.cloudinary_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )
        self.cloudinary = cloudinary

    async def _upload(self, file, prefix: str) -> str:
        public_id_prefix = prefix
        try:
            upload_result = self.cloudinary.uploader.upload(
                file,
                public_id_prefix=public_id_prefix,
                overwrite=True,
            )
            if prefix == CLOUDINARY_AVATAR_PUBLIC_ID_PREFIX:
                return (
                    cloudinary.CloudinaryImage(
                        upload_result.get("public_id")
                    ).build_url(
                        width=AVATAR_WIDTH,
                        height=AVATAR_HEIGHT,
                        crop="fill",
                        version=upload_result.get("version"),
                    )
                    + ".jpg"
                )
            return upload_result["secure_url"]
        except Exception as e:
            logger.error(e)
            raise PhotoStorageProviderError(e)

    async def _delete(self, prefix: str, file_url: str):
        try:
            file_public_id = f"{prefix}/{file_url.split('/')[-1].split('.')[0]}"
            self.cloudinary.uploader.destroy(file_public_id, invalidate=True)
        except Exception as e:
            logger.error(e)
            raise PhotoStorageProviderError(detail="Photo storage provider error")

    async def upload_photo(self, photo: File) -> str:
        return await self._upload(photo.file, CLOUDINARY_PHOTO_PUBLIC_ID_PREFIX)

    async def upload_avatar(self, avatar: File) -> str:
        return await self._upload(avatar.file, CLOUDINARY_AVATAR_PUBLIC_ID_PREFIX)

    async def delete_photo(self, photo_url: str):
        await self._delete(CLOUDINARY_PHOTO_PUBLIC_ID_PREFIX, photo_url)

    async def delete_avatar(self, avatar_url: str):
        await self._delete(CLOUDINARY_AVATAR_PUBLIC_ID_PREFIX, avatar_url)

    async def transform_photo(
        self, photo_url: str, transform: TransformIn
    ) -> (str, list[str]):
        """
        Function to perform transformations on a photo.

        Args:
             photo (PhotoOut): Photo to be transformed.
             transform (TransformIn): Transformation parameters.

        Returns:
            tuple (str, list[str]): the transformation url and the list of transformation parameters.
        """
        try:
            params = []
            if transform.background:
                params.append({"background": transform.background})
            if transform.angle:
                params.append({"angle": transform.angle})
            if transform.width:
                params.append({"width": transform.width})
            if transform.height:
                params.append({"height": transform.height})
            if transform.crop:
                params.append({"crop": transform.crop})
            if transform.effects:
                for effect in transform.effects:
                    params.append({"effect": effect})
            if not params:
                raise NotFoundError(
                    detail="No valid transformation parameters were provided.",
                )
            photo_public_id = f"{CLOUDINARY_PHOTO_PUBLIC_ID_PREFIX}/{photo_url.split('/')[-1].split('.')[0]}"
            transform_url = cloudinary.utils.cloudinary_url(
                photo_public_id, transformation=params
            )[0]
            return transform_url, params
        except Exception as e:
            logger.error(e)
            raise PhotoStorageProviderError(detail="Photo storage provider error")

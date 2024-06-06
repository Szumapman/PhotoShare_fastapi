from io import BytesIO

import cloudinary
import cloudinary.uploader
from fastapi import File
import qrcode

from src.services.abstract import AbstractPhotoStorageProvider
from src.conf.config import settings
from src.conf.constant import CLOUDINARY_PHOTO_PUBLIC_ID_PREFIX
from src.conf.logger import logger
from src.conf.errors import PhotoStorageProviderError


class CloudinaryPhotoStorageProvider(AbstractPhotoStorageProvider):
    def __init__(self):
        self.config = cloudinary.config(
            cloud_name=settings.cloudinary_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )
        self.cloudinary = cloudinary

    async def _upload(self, file) -> str:
        try:
            upload_result = self.cloudinary.uploader.upload(
                file,
                public_id_prefix=CLOUDINARY_PHOTO_PUBLIC_ID_PREFIX,
                overwrite=True,
            )
            return upload_result["secure_url"]
        except Exception as e:
            logger.error(e)
            raise PhotoStorageProviderError(e)

    async def upload_photo(self, photo: File) -> str:
        return await self._upload(photo.file)

    async def create_qr_code(self, photo_url: str) -> str:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(photo_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        return await self._upload(qr_buffer)
